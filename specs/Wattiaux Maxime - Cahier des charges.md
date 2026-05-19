# Specifications: Commercial Management & Logistics Application (Odoo-Light)
 
## 1. Product and Warehouse Management
### Register a Product
A product consists of:
*   SKU (Unique reference, e.g., `IPH-16-BLK`)
*   Name
*   Unit Price Ex-VAT (Before taxes)
*   Default VAT Rate
 
**Business Rules:**
*   The unit price ex-VAT must be strictly greater than 0.
*   The default VAT rate is set to **21.00%** by default (Belgian Standard).
 
### Create a Warehouse
A warehouse consists of:
*   Name and City
*   Type (Central, Proximity, Hub)
*   Maximum Capacity (Maximum total number of stockable items)
 
**Business Rules:**
*   The maximum capacity must be strictly greater than 0.
 
---
 
## 2. Order Management
### Create an Order
An order consists of:
*   Associated Customer
*   Assigned Warehouse (for fulfillment/shipping)
*   Status (Draft, Validated, Cancelled)
*   Order Date
 
**Business Rules:**
*   **Initial Status:** Upon creation, the order must automatically be set to **"Draft"**.
*   **Stock Inertia:** Warehouse stocks are not modified as long as the order remains in "Draft" status.
 
### Delete or Modify an Order
**Business Rules:**
*   **Modification Condition:** An order can only be modified or deleted if its status is **"Draft"**. Once it transitions to "Validated", it becomes legally binding and immutable.
 
---
 
## 3. Display and Consultation
### Order List
Display the latest non-closed orders in descending order of creation:
*   Order ID, Customer Name, Assigned Warehouse, Date, Total Item Count, Status.
*   *Bonus: Search filters (by status, customer, warehouse).*
 
### Stock Status and Alerts
Present the list of products along with their available quantities per warehouse:
*   **Stockout Alert:** Visual alert if a product's stock drops to 0.
*   **Saturation Alert:** Display of each warehouse's filling rate relative to its maximum capacity.
 
---
 
## 4. Validation and Financial Flow
### Validate an Order
**Business Rules (Blocking Conditions):**
*   **Logistics Restriction:** A warehouse typed as "Central" cannot directly ship an order to a customer. Only "Proximity" or "Hub" warehouses are permitted for direct fulfillment.
*   **Stock Availability:** For each product in the order, the requested quantity must be $\le$ to the available quantity in the assigned warehouse.
 
### Invoice Generation
If all blocking conditions are satisfied, the system updates the order status to **"Validated"** and automatically generates an invoice (1-to-1 relationship):
*   **Financial Calculations:**
    *   Total Ex-VAT = Sum of (Quantity x Unit Price Ex-VAT)
    *   VAT Amount = Sum of (Quantity x Unit Price Ex-VAT x (VAT Rate / 100))
    *   Total Inc-VAT = Total Ex-VAT + VAT Amount
*   **Invoice Status:** The status is initialized to **"Pending Payment"**.
 
---
 
## 5. Stock Movements and Logistics
### Transfer Stock (Inter-Warehouse)
A transfer consists of: a Product, a Source Warehouse, a Destination Warehouse, and a Quantity.
 
**Business Rules (Blocking Conditions):**
*   **Source Sufficiency:** The source warehouse must hold a product quantity $\ge$ to the quantity to be transferred.
*   **Destination Capacity:** The sum of all current item quantities in the destination warehouse + the transferred quantity must not exceed that warehouse's `maximum capacity`.
 
### Flow Traceability & Audit Trail
Every order validation (stock dispatch), inter-warehouse transfer, or manual stock update generates an immutable history log line:
*   **Movement ID:** Unique identifier.
*   **Product:** The item being moved.
*   **Source Warehouse:** NULL if external supplier intake.
*   **Destination Warehouse:** NULL if direct customer sale.
*   **Quantity:** Total units moved.
*   **Movement Type:** Standardized category flag (`SALE`, `TRANSFER`, `SUPPLIER_RECEPTION`, `ADJUSTMENT`).
*   **Reason:** Contextual text string providing human or system context (e.g., *"Order #12 Validation"*, *"Damaged palette during transit"*).
*   **Movement Date:** Timestamp of the event.