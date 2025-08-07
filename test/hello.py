def greet(name: str, uppercase: bool = False) -> str:
    greeting = f"Hello, {name}!"
    return greeting.upper() if uppercase else greeting

def farewell(name: str) -> str:
    return f"Goodbye, {name}."

if __name__ == "__main__":
    print(greet("World"))
    print(farewell("World"))