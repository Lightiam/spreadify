# Deployment Instructions for Spreadify Application on General PHP Hosting

## Prerequisites
- Ensure your hosting provider supports PHP 8.0 or higher.
- Ensure your hosting provider supports PostgreSQL databases.
- Have access to a control panel or SSH to upload files and manage the server.

## Application Setup

1. **Upload Application Files:**
   - Extract the `spreadify_application.zip` file.
   - Upload all files to the root directory of your hosting account using FTP or a file manager.

2. **Database Setup:**
   - Create a new PostgreSQL database using your hosting provider's control panel.
   - Import the `install/database.sql` file into your PostgreSQL database to set up the necessary tables.

3. **Environment Configuration:**
   - Rename the `.env.example` file to `.env`.
   - Update the `.env` file with your database credentials and other necessary configurations:
     ```plaintext
     database.default.hostname = 'your_db_host'
     database.default.database = 'your_db_name'
     database.default.username = 'your_db_user'
     database.default.password = 'your_db_password'
     ```

4. **Install Dependencies:**
   - If your hosting provider supports SSH access, navigate to the application directory and run `composer install` to install the necessary PHP dependencies.

## Web Server Configuration

1. **Document Root:**
   - Ensure the document root is set to the `public` directory of the application. This is where the `index.php` file is located.

2. **Apache Configuration (if applicable):**
   - If using Apache, ensure the `.htaccess` file is present in the `public` directory to handle URL rewriting.

## Running the Application

1. **Access the Application:**
   - Open a web browser and go to your domain to access the Spreadify application.

2. **Verify Functionality:**
   - Ensure that the application is functioning correctly and that all features are working as expected.

## Additional Notes
- Ensure that the PostgreSQL service is running and accessible from your hosting environment.
- If you encounter any issues, check the application logs located in the `writable/logs` directory for more information.
- Contact your hosting provider's support if you need assistance with server configurations or database setup.

Please let me know if you have any questions or need further assistance.
