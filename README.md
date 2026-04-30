# Bakery Quick Production

bakery_quick_production
This module provides a simplified "Kiosk Mode" interface for bakers and other production staff to quickly register production in Odoo. It streamlines the manufacturing process by offering a user-friendly dashboard and a quick production wizard.

## Features

*   **Simplified Dashboard:** A visual Kanban dashboard displaying relevant products for the logged-in user.
*   **Role-Based Filtering:**
    *   **Admins:** Have access to all products on the dashboard.
    *   **Production Staff:** See only products belonging to their assigned "Production Category" (configured in User Settings).
*   **Quick Production Wizard:**
    *   Clicking a product on the dashboard opens a wizard.
    *   Enter the quantity to produce.
    *   Automatically calculates required ingredients based on the Bill of Materials (BOM).
*   **One-Click Production:**
    *   **Confirm:** Immediately creates the Manufacturing Order (MO), confirms it, and marks it as "Done".
    *   **To Close:** Creates and confirms the MO but leaves it in an open state for later completion.
*   **Bulk Production:** Tools to handle multiple production orders efficiently.

## Configuration

### User Setup
To configure which products a user can see and produce:

1.  Go to **Settings > Users & Companies > Users**.
2.  Select the user you want to configure.
3.  In the **Preferences** (or relevant) tab, find the **Production Category** field.
4.  Select the specific product category (e.g., "Bakery", "Coffee", "Pastry") this user is responsible for.
    *   *Note: If no category is selected, the user will not see any products on the dashboard (unless they are an Admin).*

## Usage

1.  **Navigate to the Dashboard:** Open the "Bakery Production" app from the main menu.
2.  **Select a Product:** Click on the product card you wish to produce.
3.  **Enter Quantity:** In the popup wizard, enter the `Quantity to Produce`.
    *   The ingredient list will update automatically based on the BOM.
4.  **Register Production:**
    *   Click **Confirm** to finish the production immediately.
    *   Click **To Close** if you want to start the production but finish it later.

## Technical Details

*   **Dependencies:** `mrp`, `stock`, `product`
*   **Models Extended:** `res.users` (added `production_category_id`)
*   **New Models:** `bakery.production.wizard`, `bakery.production.list`
