from concurrent.futures import ThreadPoolExecutor

# Limit concurrent AI jobs (important!)
agent_executor = ThreadPoolExecutor(max_workers=4)
