def version():
    with open('VERSION') as f:
        data = f.read()
        return data
