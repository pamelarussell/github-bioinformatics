from time import sleep

# GitHub API rate limit
api_rate_limit_per_hour = 5000

# The number of seconds to wait between jobs if expecting to approach the rate limit
sec_between_requests = 60 * 60 / api_rate_limit_per_hour

def sleep_github_rate_limit():
    sleep(sec_between_requests + 0.001) 
    
    
