
import pandas as pd
from faker import Faker
import random, argparse
from datetime import datetime, timedelta, date

def gen(n_users=50, seed=42):
    fake = Faker()
    random.seed(seed)
    Faker.seed(seed)

    users = []
    for i in range(n_users):
        email = f"{fake.first_name().lower()}@acme.com"
        dept = random.choice(["Engineering","Sales","Marketing","Finance","Support","Design","Data"])
        status = random.choices(["active","terminated"], weights=[0.85,0.15])[0]
        users.append([email, dept, "US", status])
    users_df = pd.DataFrame(users, columns=["user_email","department","country","status"])

    products = [
        ("Microsoft 365 E3","Microsoft","subscription",36,100, "2025-01-01", "2025-12-31"),
        ("Visio Plan 2","Microsoft","subscription",15,25,"2025-03-01","2026-02-28"),
        ("SAP S/4HANA","SAP","perpetual",2500,10,"2024-07-01","2029-06-30"),
        ("Tableau Creator","Salesforce","subscription",70,12,"2025-05-01","2026-04-30"),
        ("Zoom Pro","Zoom","subscription",12,50,"2025-01-15","2026-01-14"),
    ]
    lic_df = pd.DataFrame(products, columns=["software","vendor","license_type","unit_cost_usd","seats_purchased","contract_start","contract_end"])
    lic_df["license_key"] = [f"KEY-{i:04d}" for i in range(len(lic_df))]

    installs = []
    for _, row in lic_df.iterrows():
        sw = row["software"]
        for _ in range(random.randint(int(row["seats_purchased"]*0.3), int(row["seats_purchased"]*0.9))):
            u = users_df.sample(1).iloc[0]
            last_used = date.today() - timedelta(days=random.randint(0,200))
            installs.append([f"LAP-{random.randint(1000,9999)}", u["user_email"], sw, "1.0", date.today(), last_used])
    inst_df = pd.DataFrame(installs, columns=["device_id","user_email","software","version","install_date","last_used_date"])

    return users_df, lic_df, inst_df

if __name__ == "__main__":
    users_df, lic_df, inst_df = gen()
    users_df.to_csv("data/users.csv", index=False)
    lic_df.to_csv("data/licenses.csv", index=False)
    inst_df.to_csv("data/installations.csv", index=False)
    print("Mock data written to data/*.csv")
