import os.path
import random
import json
import sys

from faker import Faker


def generate_data(n: int):
    faker = Faker()

    data_list = []
    for i in range(n):
        data = {
            "person": {
                "id": i + 1,
                "name": faker.name(),
                "email": faker.email(),
            },
            "description": faker.text(),
            "currency": random.choice(["COP", "USD", "EUR"]),
            "amount": random.randint(1500, 9500)
        }
        data_list.append(data)

    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "data.json"), "w") as f:
        f.write(json.dumps(data_list, indent=2))


if __name__ == "__main__":
    cant = int(sys.argv[1])
    generate_data(cant)
