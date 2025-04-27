# Deployment Instructions for LightSMS Application

## Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Firebase account with appropriate permissions
- Twilio account with API credentials
- Vercel account for deployment

## Backend Setup

1. **Firebase Configuration:**
   - Place the Firebase credentials JSON file in a secure location.
   - Rename the `.env.example` file to `.env`.
   - Update the `.env` file with your Firebase and Twilio credentials:
     ```plaintext
     # Firebase Configuration
     FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
     FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
     FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
     FIREBASE_PROJECT_ID=your-project-id

     # Twilio Configuration
     TWILIO_ACCOUNT_SID=your_account_sid
     TWILIO_AUTH_TOKEN=your_auth_token
     TWILIO_FROM_NUMBER=your_twilio_phone_number
     ```

2. **Install Dependencies:**
   - Run `composer install` to install the necessary PHP dependencies.
   - Run `npm install` to install the necessary Node.js dependencies.

## Frontend Development

1. **Local Development:**
   - Run `npm run dev` to start the Vite development server.
   - Access the application at `http://localhost:3000`.

2. **Build for Production:**
   - Run `npm run build` to create a production build.
   - The build output will be in the `dist` directory.

## Deployment to Vercel

1. **Install Vercel CLI (Optional):**
   - Run `npm install -g vercel` to install the Vercel CLI globally.

2. **Deploy Using Vercel CLI:**
   - Run `vercel login` to authenticate with your Vercel account.
   - Run `vercel` in the project directory to deploy.
   - Follow the prompts to configure your deployment.

3. **Deploy Using Vercel Dashboard:**
   - Push your code to a Git repository (GitHub, GitLab, or Bitbucket).
   - Log in to the [Vercel Dashboard](https://vercel.com/dashboard).
   - Click "New Project" and import your repository.
   - Configure the project:
     - Framework Preset: Vite
     - Build Command: `npm run build`
     - Output Directory: `dist`
     - Install Command: `npm install`
   - Set up environment variables for Firebase and Twilio in the Vercel project settings.
   - Click "Deploy" to deploy your application.

4. **Custom Domain Setup (Optional):**
   - Go to your project settings in the Vercel Dashboard.
   - Navigate to the "Domains" section.
   - Add your custom domain and follow the verification steps.

## Environment Variables in Vercel

Make sure to set the following environment variables in your Vercel project settings:

### Firebase Configuration
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase credentials JSON file
- `FIREBASE_DATABASE_URL`: Firebase database URL
- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket
- `FIREBASE_PROJECT_ID`: Firebase project ID

### Twilio Configuration
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_FROM_NUMBER`: Twilio phone number

## Continuous Deployment

Vercel automatically deploys your application when you push changes to your repository. You can configure branch deployments in the project settings.

## Additional Notes
- Ensure that your Firebase security rules are properly configured to secure your data.
- If you encounter any issues, check the Vercel deployment logs for more information.
- For Twilio-related issues, verify your credentials and check the Twilio console for logs.

Please let me know if you have any questions or need further assistance.
