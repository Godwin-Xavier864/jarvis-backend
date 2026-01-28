from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from core.models import DaySpeciality


from .models import Profile, Task, Notification, UserActivity
from .serializers import TaskSerializer, NotificationSerializer

class LoginView(APIView):
    def post(self, request):
        user = User.objects.filter(username=request.data.get("username")).first()
        if not user or not user.check_password(request.data.get("password")):
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_admin": user.is_staff
        })


class AdminCreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        user = User.objects.create_user(
            username=request.data['username'],
            password=request.data['password']
        )

        Profile.objects.create(
            user=user,
            designation=request.data['designation']
        )

        return Response({"message": "User created"})


class AdminCreateTaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        amount = request.data.get("amount_paid")

        task = Task.objects.create(
            title=request.data.get("title"),
            description=request.data.get("description"),
            amount_paid=amount if amount not in ("", None) else None,
            deadline=request.data.get("deadline"),
            assigned_to=User.objects.get(id=request.data.get("assigned_to")),
        )

        return Response(
            {"task_id": task.id},
            status=201,
        )



class UserTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        return Response(TaskSerializer(tasks, many=True).data)


class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = Task.objects.get(id=task_id, assigned_to=request.user)
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        return Response({"message": "Task completed"})


class AdminNotificationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        Notification.objects.create(
            title=request.data['title'],
            message=request.data['message'],
            is_important=request.data.get('is_important', False),
            is_plan=request.data.get('is_plan', False)
        )
        return Response({"message": "Notification added"})

class UserNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(NotificationSerializer(Notification.objects.all(), many=True).data)


class AppOpenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = timezone.now().date()
        UserActivity.objects.get_or_create(user=request.user, date=today)

        cutoff = today - timedelta(days=7)
        UserActivity.objects.filter(date__lt=cutoff).delete()

        return Response({"message": "Activity logged"})


class AdminActivityView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        data = UserActivity.objects.select_related('user').values(
            'user__username', 'date'
        )
        return Response(data)


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.select_related().all()

        data = []
        for user in users:
            profile = Profile.objects.filter(user=user).first()

            data.append({
                "id": user.id,
                "username": user.username,
                "designation": profile.designation if profile else None,
                "is_admin": user.is_staff,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
            })

        return Response(data)
    
    
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


import uuid
import traceback

from django.db import close_old_connections

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AgentChat
from core.agent.permissions import get_agent_capabilities
from core.agent.context import build_user_context, build_admin_context
from core.agent.groq_client import run_groq_agent
from core.agent.executor import agent_executor


class AgentChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message cannot be empty"},
                status=400,
            )

        task_id = str(uuid.uuid4())

        # 1️⃣ Save user message
        AgentChat.objects.create(
            user=user,
            role="user",
            content=message,
            task_id=task_id,
        )

        # 2️⃣ Detect if message needs DAY SPECIALITY
        speciality_keywords = [
            "today special",
            "today speciality",
            "tomorrow special",
            "tomorrow speciality",
            "special day",
            "festival",
            "holiday",
            "create poster",
            "poster for today",
            "poster for tomorrow",
        ]

        needs_speciality = any(
            kw in message.lower() for kw in speciality_keywords
        )

        # 3️⃣ Determine scope (ADMIN vs USER)
        is_admin = user.is_staff

        if is_admin:
            context = build_admin_context()
            system_prompt = """
You are Jarvis, an internal admin assistant.

You can:
- Summarize tasks, users, reports, client leads, and activity
- Answer operational questions for admins
- Help analyze workloads and issues

Rules:
- Never mention databases, tables, ORM, SQL, schemas, or backend code
- Never invent data
- If something is unavailable, say so clearly
- Respond concisely and professionally
- If data shows user name "SIR" it is the admin so call him sir
"""
        else:
            context = build_user_context(user)
            system_prompt = """
You are Jarvis, a personal assistant for a user.

You can:
- Explain the user's tasks
- Summarize notifications
- Answer general questions

Rules:
- Only use the user's own data
- Never mention internal systems or databases
- Be friendly and clear
"""

        # 4️⃣ Build AI messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # 🔥 Inject DAY SPECIALITY ONLY WHEN ASKED
        if needs_speciality:
            today = timezone.now().date()
            tomorrow = today + timedelta(days=1)

            today_special = DaySpeciality.objects.filter(date=today).first()
            tomorrow_special = DaySpeciality.objects.filter(date=tomorrow).first()

            speciality_context = {
                "today": {
                    "date": str(today),
                    "title": today_special.title if today_special else None,
                    "description": today_special.description if today_special else None,
                    "poster_hint": today_special.poster_hint if today_special else None,
                },
                "tomorrow": {
                    "date": str(tomorrow),
                    "title": tomorrow_special.title if tomorrow_special else None,
                    "description": tomorrow_special.description if tomorrow_special else None,
                    "poster_hint": tomorrow_special.poster_hint if tomorrow_special else None,
                },
            }

            messages.append({
                "role": "system",
                "content": f"DAY SPECIALITIES:\n{speciality_context}"
            })

        # 5️⃣ Inject normal context (always)
        messages.append({
            "role": "system",
            "content": f"AVAILABLE DATA:\n{context}"
        })

        # 6️⃣ Conversation history (last 10)
        history = (
            AgentChat.objects
            .filter(user=user)
            .order_by("-created_at")[:10]
        )

        for h in reversed(history):
            messages.append(
                {"role": h.role, "content": h.content}
            )

        # 7️⃣ Background AI execution
        def background_job():
            try:
                close_old_connections()

                response = run_groq_agent(messages)

                AgentChat.objects.create(
                    user=user,
                    role="assistant",
                    content=response,
                    task_id=task_id,
                )

            except Exception:
                traceback.print_exc()

                AgentChat.objects.create(
                    user=user,
                    role="assistant",
                    content=(
                        "I'm having trouble accessing the system right now. "
                        "Please try again in a moment."
                    ),
                    task_id=task_id,
                )

        agent_executor.submit(background_job)

        return Response(
            {
                "task_id": task_id,
                "status": "processing",
            },
            status=200,
        )


class AgentResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        chat = (
            AgentChat.objects.filter(
                user=request.user,
                role="assistant",
                task_id=task_id,
            )
            .order_by("-created_at")
            .first()
        )

        if chat:
            return Response({"response": chat.content})

        return Response({"status": "processing"})




from core.models import ClientLead
from core.serializers import ClientLeadSerializer

class ClientLeadListCreateView(APIView):
    """
    GET  -> List all client leads of logged-in user
    POST -> Create new client lead
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leads = ClientLead.objects.filter(user=request.user).order_by("-created_at")
        serializer = ClientLeadSerializer(leads, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClientLeadSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                user=request.user,
                created_by=request.user,  # ✅ SET ONCE (never updated)
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )






from core.models import ClientLead
from core.serializers import ClientLeadSerializer


class ClientLeadDetailView(APIView):
    """
    GET    -> View one lead
    PUT    -> Update ALL fields
    PATCH  -> Update ONLY status (safe)
    DELETE -> Delete lead
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return ClientLead.objects.get(pk=pk, user=request.user)

    def get(self, request, pk):
        lead = self.get_object(request, pk)
        serializer = ClientLeadSerializer(lead)
        return Response(serializer.data)

    def put(self, request, pk):
        lead = self.get_object(request, pk)
        serializer = ClientLeadSerializer(lead, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ FIXED PATCH (STATUS ONLY)
    def patch(self, request, pk):
        lead = self.get_object(request, pk)

        status_value = request.data.get("status")

        if not status_value:
            return Response(
                {"error": "status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if status_value not in dict(ClientLead.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead.status = status_value
        lead.save(update_fields=["status", "updated_at"])

        serializer = ClientLeadSerializer(lead)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        lead = self.get_object(request, pk)
        lead.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
from decimal import Decimal, InvalidOperation
from rest_framework import status
from django.shortcuts import get_object_or_404


class AdminUpdateTaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        # Optional fields (partial update)
        title = request.data.get("title")
        description = request.data.get("description")
        deadline = request.data.get("deadline")
        status_val = request.data.get("status")
        amount_paid = request.data.get("amount_paid")

        if title is not None:
            task.title = title

        if description is not None:
            task.description = description

        if deadline is not None:
            task.deadline = deadline

        if status_val is not None:
            task.status = status_val

        if amount_paid is not None:
            # allow null or decimal
            if amount_paid == "":
                task.amount_paid = None
            else:
                try:
                    task.amount_paid = Decimal(amount_paid)
                except (InvalidOperation, TypeError):
                    return Response(
                        {"error": "amount_paid must be a number or null"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        task.save()

        return Response(
            {
                "message": "Task updated successfully",
                "task_id": task.id,
            },
            status=status.HTTP_200_OK,
        )


class AdminTaskListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tasks = (
            Task.objects
            .select_related("assigned_to")
            .all()
            .order_by('-id')  # ⬅️ retyped dash
        )

        data = []
        for t in tasks:
            data.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "deadline": t.deadline,
                "status": t.status,
                "amount_paid": t.amount_paid,
                "assigned_to": t.assigned_to.id if t.assigned_to else None,
                "assigned_to_username": (
                    t.assigned_to.username if t.assigned_to else None
                ),
            })

        return Response(data)


from core.models import UserReport
from core.serializers import UserReportSerializer


class UserReportCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = (
            UserReport.objects
            .filter(user=request.user)
            .order_by("-created_at")
        )
        serializer = UserReportSerializer(reports, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
class AdminReportListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        reports = UserReport.objects.select_related("user").order_by("-created_at")
        serializer = UserReportSerializer(reports, many=True)
        return Response(serializer.data)

from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import DaySpeciality
from core.serializers import DaySpecialitySerializer
from core.day_speciality_fetcher import fetch_day_speciality_from_api


class TodayTomorrowSpecialityView(APIView):
    permission_classes = [IsAuthenticated]

    def get_or_create_speciality(self, date):
        # 1️⃣ Check DB
        speciality = DaySpeciality.objects.filter(date=date).first()
        if speciality:
            return speciality

        # 2️⃣ Fetch from API
        fetched = fetch_day_speciality_from_api(date)

        if not fetched:
            return None

        # 3️⃣ Save to DB
        return DaySpeciality.objects.create(
            date=date,
            title=fetched["title"],
            description=fetched["description"],
            poster_hint=fetched["poster_hint"],
        )

    def get(self, request):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        today_special = self.get_or_create_speciality(today)
        tomorrow_special = self.get_or_create_speciality(tomorrow)

        return Response({
            "today": (
                DaySpecialitySerializer(today_special).data
                if today_special else None
            ),
            "tomorrow": (
                DaySpecialitySerializer(tomorrow_special).data
                if tomorrow_special else None
            ),
        })


class AdminUpdateUserPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request):
        username = request.data.get("username")
        new_password = request.data.get("password")

        if not username or not new_password or len(new_password) < 6:
            return Response(
                {"error": "Username and password (min 6 chars) required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, username=username)

        user.set_password(new_password)  # ✅ hashed properly
        user.save()

        return Response(
            {
                "message": f"Password updated successfully for user '{user.username}'"
            },
            status=status.HTTP_200_OK,
        )


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return render(request, "admin_login.html")

        if not user.is_staff:
            messages.error(request, "You are not an admin")
            return render(request, "admin_login.html")

        login(request, user)  # ✅ Django session login
        return redirect("/admin-dashboard/")  # change if needed

    return render(request, "core/admin_login.html")


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from core.models import Notification, ClientLead, UserReport

def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    context = {
        "notifications": Notification.objects.order_by("-id"),
        "reports": UserReport.objects.select_related("user").order_by("-created_at"),
        "clients": ClientLead.objects.select_related("user").order_by("-created_at"),
    }
    return render(request, "core/admin_dashboard.html", context)



from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect

@login_required(login_url="/admin-login/")
@user_passes_test(lambda u: u.is_staff)
def admin_update_password_view(request):
    if request.method == "POST":
        new_password = request.POST.get("password")

        if not new_password or len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect("/admin-dashboard/")

        request.user.set_password(new_password)
        request.user.save()

        messages.success(request, "Password updated successfully. Please login again.")
        return redirect("/admin-login/")

    return redirect("/admin-dashboard/")


@login_required
@user_passes_test(is_admin)
def admin_delete_notification(request, id):
    Notification.objects.filter(id=id).delete()
    messages.success(request, "Notification deleted")
    return redirect("/admin-dashboard/")

@login_required
@user_passes_test(is_admin)
def admin_delete_report(request, id):
    UserReport.objects.filter(id=id).delete()
    messages.success(request, "Report deleted")
    return redirect("/admin-dashboard/")

@login_required
@user_passes_test(is_admin)
def admin_delete_client(request, id):
    ClientLead.objects.filter(id=id).delete()
    messages.success(request, "Client deleted")
    return redirect("/admin-dashboard/")
