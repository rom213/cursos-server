from concurrent.futures import ThreadPoolExecutor

# Create a global executor
# Adjust max_workers as needed based on server resources
executor = ThreadPoolExecutor(max_workers=3)
