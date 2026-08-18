

CREATE TABLE expense_categories (

    id SERIAL PRIMARY KEY,

    category_name VARCHAR(100) NOT NULL UNIQUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);



CREATE TABLE expenses (

    id SERIAL PRIMARY KEY,

    expense_number VARCHAR(20) UNIQUE NOT NULL,

    expense_date DATE NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    category_id INTEGER NOT NULL,

    amount NUMERIC(10,2) NOT NULL,

    payment_method VARCHAR(30) NOT NULL CHECK (
        payment_method IN (
            'Cash',
            'UPI',
            'Bank Transfer',
            'Debit Card',
            'Credit Card'
        )
    ),

    receipt BYTEA,

    receipt_name VARCHAR(255),

    receipt_type VARCHAR(100),

    status VARCHAR(20) DEFAULT 'Pending' CHECK (
        status IN (
            'Pending',
            'Approved',
            'Rejected',
            'Paid'
        )
    ),

    created_by INTEGER NOT NULL,

    approved_by INTEGER,

    approved_at TIMESTAMP,

    paid_at TIMESTAMP,

    remarks TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_expense_category
        FOREIGN KEY (category_id)
        REFERENCES expense_categories(id)
);