cart = [
    {"name": "Laptop", "price": 50000, "quantity": 1},
    {"name": "Mouse", "price": 800, "quantity": 2},
    {"name": "Keyboard", "price": 1500, "quantity": 1}
]


def calculate_total(cart):
    total = 0

    for item in cart:
        total += item["price"] * item["quantity"]

    return total


def find_product(cart, name):
    for item in cart:
        if item["name"].lower() == name.lower():
            return item

    return None


def main():
    print("Total:", calculate_total(cart))

    name = input("Enter product name: ")

    product = find_product(cart, name)

    if product:
        print("Product:", product["name"])
        print("Price:", product["price"])

        try:
            quantity = int(input("Enter new quantity: "))
        except ValueError:
            print("Enter a Valid Number ")    
        product["quantity"] = quantity

        print("Updated total:", calculate_total(cart))

    else:
        print("Product Not Found")


main()


