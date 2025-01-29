const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-pink-500 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-xl p-8">
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
        
        <div className="space-y-6">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="text-gray-700">
              Welcome to Spreadify A. We respect your privacy and are committed to protecting your personal data.
              This privacy policy will inform you about how we look after your personal data when you visit our website
              and tell you about your privacy rights and how the law protects you.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. Data We Collect</h2>
            <p className="text-gray-700">
              We collect and process the following data:
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>Identity Data (name, username)</li>
              <li>Contact Data (email address)</li>
              <li>Technical Data (IP address, browser type and version)</li>
              <li>Profile Data (your preferences and settings)</li>
              <li>Usage Data (how you use our website and services)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Data</h2>
            <p className="text-gray-700">
              We use your data to:
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>Provide and manage your account</li>
              <li>Deliver our streaming services</li>
              <li>Process your payments</li>
              <li>Send you service updates</li>
              <li>Improve our services</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Data Security</h2>
            <p className="text-gray-700">
              We have implemented appropriate security measures to prevent your personal data from being accidentally
              lost, used, or accessed in an unauthorized way. We limit access to your personal data to those employees,
              agents, contractors, and other third parties who have a business need to know.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Your Rights</h2>
            <p className="text-gray-700">
              Under data protection laws, you have rights including:
            </p>
            <ul className="list-disc pl-6 mt-2 text-gray-700">
              <li>Right to access your personal data</li>
              <li>Right to correct your personal data</li>
              <li>Right to erasure of your personal data</li>
              <li>Right to restrict processing of your personal data</li>
              <li>Right to data portability</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Contact Us</h2>
            <p className="text-gray-700">
              If you have any questions about this privacy policy or our privacy practices, please contact us at:
              support@spreadify.app
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Changes to This Policy</h2>
            <p className="text-gray-700">
              We may update this privacy policy from time to time. We will notify you of any changes by posting the
              new privacy policy on this page and updating the "last updated" date.
            </p>
            <p className="text-gray-700 mt-4">
              Last updated: January 28, 2024
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
