ALTER TABLE expenses
    ADD COLUMN IF NOT EXISTS subcategory_id INTEGER NULL
        REFERENCES expense_subcategories(id);

ALTER TABLE expenses
    ADD COLUMN IF NOT EXISTS receipt_image BYTEA NULL;
