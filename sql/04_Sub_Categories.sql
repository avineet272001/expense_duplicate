CREATE TABLE expense_subcategories (

    id SERIAL PRIMARY KEY,

    category_id INT NOT NULL,

    subcategory_name VARCHAR(100) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_category
        FOREIGN KEY(category_id)
        REFERENCES expense_categories(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_category_subcategory
        UNIQUE(category_id, subcategory_name)
);




INSERT INTO expense_subcategories (category_id, subcategory_name)
VALUES
-- Office Supplies
(1, 'Stationery'),
(1, 'Printer Paper'),
(1, 'Ink Cartridge'),
(1, 'Pens'),
(1, 'Files'),
(1, 'Office Furniture'),

-- Transportation
(2, 'Cab'),
(2, 'Taxi'),
(2, 'Bus'),
(2, 'Train'),
(2, 'Fuel'),
(2, 'Parking'),

-- Electricity
(3, 'Office Electricity Bill'),
(3, 'Generator Fuel'),
(3, 'Power Backup'),

-- Internet
(4, 'Broadband'),
(4, 'Wi-Fi Recharge'),
(4, 'Mobile Data'),
(4, 'Internet Lease Line'),

-- Maintenance
(5, 'AC Repair'),
(5, 'Electrical Repair'),
(5, 'Plumbing'),
(5, 'Cleaning'),
(5, 'Building Maintenance'),

-- Inventory Purchase
(6, 'Raw Material'),
(6, 'Office Stock'),
(6, 'Packaging Material'),
(6, 'Spare Parts'),

-- Equipment
(7, 'Laptop'),
(7, 'Desktop'),
(7, 'Printer'),
(7, 'Monitor'),
(7, 'Keyboard'),
(7, 'Mouse'),

-- Rent
(8, 'Office Rent'),
(8, 'Warehouse Rent'),
(8, 'Parking Rent'),

-- Travel
(9, 'Flight'),
(9, 'Hotel'),
(9, 'Local Travel'),
(9, 'Food During Travel'),
(9, 'Visa'),

-- Food
(10, 'Breakfast'),
(10, 'Lunch'),
(10, 'Dinner'),
(10, 'Snacks'),
(10, 'Refreshments'),

-- Other
(11, 'Miscellaneous'),
(11, 'Courier'),
(11, 'Training'),
(11, 'Subscription');