CREATE TABLE IF NOT EXISTS Customers (
    CustomerID SERIAL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID SERIAL PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Price NUMERIC(10, 2) NOT NULL CHECK (Price > 0)
);

CREATE TABLE IF NOT EXISTS Orders (
    OrderID SERIAL PRIMARY KEY,
    CustomerID INT NOT NULL REFERENCES Customers(CustomerID),
    OrderDate TIMESTAMP NOT NULL DEFAULT NOW(),
    TotalAmount NUMERIC(10, 2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS OrderItems (
    OrderItemID SERIAL PRIMARY KEY,
    OrderID INT NOT NULL REFERENCES Orders(OrderID),
    ProductID INT NOT NULL REFERENCES Products(ProductID),
    Quantity INT NOT NULL CHECK (Quantity > 0),
    Subtotal NUMERIC(10, 2) NOT NULL CHECK (Subtotal >= 0)
);

INSERT INTO Customers (FirstName, LastName, Email) VALUES
    ('Alice', 'Johnson', 'alice@example.com'),
    ('Bob', 'Smith', 'bob@example.com')
ON CONFLICT (Email) DO NOTHING;

INSERT INTO Products (ProductName, Price) VALUES
    ('Laptop', 999.99),
    ('Mouse', 25.50),
    ('Keyboard', 75.00)
ON CONFLICT DO NOTHING;
