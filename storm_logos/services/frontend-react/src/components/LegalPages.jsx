import './LegalPages.css'

export function TermsPage() {
  return (
    <div className="legal-page">
      <div className="legal-content">
        <a href="/" className="legal-back">&larr; Back to Home</a>
        <h1>Terms of Service</h1>
        <p className="legal-updated">Last updated: January 2026</p>

        <section>
          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing and using Dream Engine ("the Service"), you agree to be bound by these
            Terms of Service. If you do not agree to these terms, please do not use the Service.
          </p>
        </section>

        <section>
          <h2>2. Description of Service</h2>
          <p>
            Dream Engine is an experimental AI-powered platform for exploring ideas through
            conversational interaction. The Service is provided "as is" for research and
            educational purposes.
          </p>
        </section>

        <section>
          <h2>3. User Accounts</h2>
          <p>
            You are responsible for maintaining the confidentiality of your account credentials
            and for all activities that occur under your account. You must provide accurate
            information when creating an account.
          </p>
        </section>

        <section>
          <h2>4. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul>
            <li>Use the Service for any unlawful purpose</li>
            <li>Attempt to gain unauthorized access to the Service</li>
            <li>Interfere with or disrupt the Service</li>
            <li>Use the Service to generate harmful or misleading content</li>
          </ul>
        </section>

        <section>
          <h2>5. Intellectual Property</h2>
          <p>
            The Service and its original content, features, and functionality are owned by
            Dream Engine and are protected by international copyright and other intellectual
            property laws.
          </p>
        </section>

        <section>
          <h2>6. Limitation of Liability</h2>
          <p>
            The Service is provided without warranties of any kind. We shall not be liable
            for any indirect, incidental, special, or consequential damages resulting from
            your use of the Service.
          </p>
        </section>

        <section>
          <h2>7. Changes to Terms</h2>
          <p>
            We reserve the right to modify these terms at any time. We will notify users of
            significant changes. Continued use of the Service after changes constitutes
            acceptance of the new terms.
          </p>
        </section>

        <section>
          <h2>8. Contact</h2>
          <p>
            For questions about these Terms, please contact us through the Service.
          </p>
        </section>
      </div>
    </div>
  )
}

export function PrivacyPage() {
  return (
    <div className="legal-page">
      <div className="legal-content">
        <a href="/" className="legal-back">&larr; Back to Home</a>
        <h1>Privacy Policy</h1>
        <p className="legal-updated">Last updated: January 2026</p>

        <section>
          <h2>1. Information We Collect</h2>
          <p>We collect information you provide directly:</p>
          <ul>
            <li><strong>Account Information:</strong> Username, email address, and password (encrypted)</li>
            <li><strong>Usage Data:</strong> Conversation history and interactions with the Service</li>
            <li><strong>Technical Data:</strong> Browser type, IP address, and access times</li>
          </ul>
        </section>

        <section>
          <h2>2. How We Use Your Information</h2>
          <p>We use collected information to:</p>
          <ul>
            <li>Provide and maintain the Service</li>
            <li>Improve and personalize your experience</li>
            <li>Communicate with you about the Service</li>
            <li>Ensure security and prevent abuse</li>
          </ul>
        </section>

        <section>
          <h2>3. Data Storage and Security</h2>
          <p>
            Your data is stored securely using industry-standard encryption. We implement
            appropriate technical and organizational measures to protect your personal information.
          </p>
        </section>

        <section>
          <h2>4. Data Sharing</h2>
          <p>
            We do not sell your personal information. We may share data only:
          </p>
          <ul>
            <li>With your consent</li>
            <li>To comply with legal obligations</li>
            <li>To protect our rights and safety</li>
          </ul>
        </section>

        <section>
          <h2>5. Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li>Access your personal data</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your data</li>
            <li>Export your data</li>
          </ul>
        </section>

        <section>
          <h2>6. Cookies</h2>
          <p>
            We use essential cookies to maintain your session and preferences. We do not use
            tracking cookies for advertising purposes.
          </p>
        </section>

        <section>
          <h2>7. Third-Party Services</h2>
          <p>
            The Service may integrate with third-party AI providers. Your interactions may be
            processed according to their respective privacy policies.
          </p>
        </section>

        <section>
          <h2>8. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of any
            changes by posting the new policy on this page.
          </p>
        </section>

        <section>
          <h2>9. Contact Us</h2>
          <p>
            If you have questions about this Privacy Policy, please contact us through the Service.
          </p>
        </section>
      </div>
    </div>
  )
}
