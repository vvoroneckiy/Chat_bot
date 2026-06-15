import os
import time
from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import (
    declarative_base, sessionmaker, relationship, Session
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "store")
DB_USER = os.getenv("DB_USER", "store_user")
DB_PASS = os.getenv("DB_PASS", "store_pass")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

Base = declarative_base()


class Customer(Base):
    __tablename__ = "Customers"

    CustomerID = Column(Integer, primary_key=True)
    FirstName = Column(String(50), nullable=False)
    LastName = Column(String(50), nullable=False)
    Email = Column(String(100), unique=True, nullable=False)


class Product(Base):
    __tablename__ = "Products"

    ProductID = Column(Integer, primary_key=True)
    ProductName = Column(String(100), nullable=False)
    Price = Column(Numeric(10, 2), nullable=False)


class Order(Base):
    __tablename__ = "Orders"

    OrderID = Column(Integer, primary_key=True)
    CustomerID = Column(Integer, ForeignKey("Customers.CustomerID"), nullable=False)
    OrderDate = Column(DateTime, nullable=False, default=datetime.now)
    TotalAmount = Column(Numeric(10, 2), nullable=False, default=0)

    customer = relationship("Customer")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "OrderItems"

    OrderItemID = Column(Integer, primary_key=True)
    OrderID = Column(Integer, ForeignKey("Orders.OrderID"), nullable=False)
    ProductID = Column(Integer, ForeignKey("Products.ProductID"), nullable=False)
    Quantity = Column(Integer, nullable=False)
    Subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


def seed_data(session: Session):
    if not session.query(Customer).first():
        session.add_all([
            Customer(FirstName="Alice", LastName="Johnson", Email="alice@example.com"),
            Customer(FirstName="Bob", LastName="Smith", Email="bob@example.com"),
        ])
    if not session.query(Product).first():
        session.add_all([
            Product(ProductName="Laptop", Price=Decimal("999.99")),
            Product(ProductName="Mouse", Price=Decimal("25.50")),
            Product(ProductName="Keyboard", Price=Decimal("75.00")),
        ])
    session.commit()


def wait_for_db(engine, max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                raise e


def scenario_1_place_order(session: Session, customer_id: int, products: list[dict]):
    items_data = []
    total = Decimal("0.00")

    for item in products:
        product_id = item["product_id"]
        quantity = item["quantity"]
        product = session.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found")
        subtotal = product.Price * quantity
        items_data.append((product_id, quantity, subtotal))
        total += subtotal

    order = Order(
        CustomerID=customer_id,
        OrderDate=datetime.now(),
        TotalAmount=Decimal("0.00"),
    )
    session.add(order)
    session.flush()

    for product_id, quantity, subtotal in items_data:
        order_item = OrderItem(
            OrderID=order.OrderID,
            ProductID=product_id,
            Quantity=quantity,
            Subtotal=subtotal,
        )
        session.add(order_item)

    order.TotalAmount = total

    print(f"  [OK] Order #{order.OrderID} placed, total = {total}")


def scenario_2_update_email(session: Session, customer_id: int, new_email: str):
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise ValueError(f"Customer {customer_id} not found")
    customer.Email = new_email
    print(f"  [OK] Customer #{customer_id} email updated to {new_email}")


def scenario_3_add_product(session: Session, name: str, price: Decimal):
    product = Product(ProductName=name, Price=price)
    session.add(product)
    session.flush()
    print(f"  [OK] Product #{product.ProductID} '{name}' added at ${price}")


def print_table(session: Session, model, label: str):
    rows = session.query(model).all()
    print(f"\n{label}:")
    for r in rows:
        vals = ", ".join(
            f"{c.name}={getattr(r, c.name)}"
            for c in model.__table__.columns
        )
        print(f"  {vals}")


def main():
    engine = create_engine(DATABASE_URL)
    wait_for_db(engine)

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        seed_data(session)
        try:
            print("=== SCENARIO 1: Place an order ===")
            scenario_1_place_order(
                session,
                customer_id=1,
                products=[
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 2, "quantity": 2},
                    {"product_id": 3, "quantity": 1},
                ],
            )

            print("\n=== SCENARIO 2: Update customer email ===")
            scenario_2_update_email(session, 1, "alice.new@example.com")

            print("\n=== SCENARIO 3: Add a new product ===")
            scenario_3_add_product(session, "Monitor 4K", Decimal("299.99"))

            session.commit()
            print("\n=== All transactions committed successfully ===")

            print_table(session, Customer, "Customers")
            print_table(session, Product, "Products")
            print_table(session, Order, "Orders")
            print_table(session, OrderItem, "OrderItems")

        except Exception as e:
            session.rollback()
            print(f"\n[ERROR] Transaction rolled back: {e}")
            raise


if __name__ == "__main__":
    main()
