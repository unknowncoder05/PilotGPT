def fibonacci_cows(n):
    cows = ["🐮", "🐄"]  # list of cows
    for i in range(n):
        # append the sum of the previous two cows
        cows.append(cows[-1] + cows[-2])
    return cows
