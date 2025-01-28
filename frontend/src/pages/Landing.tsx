import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-gradient-to-br from-purple-100 via-purple-50 to-white -z-10 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/4"></div>
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-pink-100 via-purple-50 to-white -z-10 rounded-full blur-3xl transform -translate-x-1/2 translate-y-1/4"></div>

      <div className="container mx-auto px-4 py-8">
        <nav className="flex justify-between items-center mb-16">
          <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Spreadify AI
          </div>
          <div className="space-x-4">
            <Button variant="ghost" className="text-gray-700 hover:text-gray-900" asChild>
              <Link to="/login">Sign In</Link>
            </Button>
            <Button className="bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700" asChild>
              <Link to="/pricing">Get Started</Link>
            </Button>
          </div>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center py-16">
          <div className="text-center lg:text-left">
            <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Professional Live Streaming
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent"> Made Easy</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Stream to multiple platforms simultaneously, collaborate with guests,
              and create engaging content with our powerful studio tools.
            </p>
            
            {/* Ratings and social proof */}
            <div className="flex flex-wrap gap-8 mb-8">
              <div className="flex items-center">
                <div className="mr-2">
                  <div className="text-2xl font-bold text-gray-900">4.9</div>
                  <div className="flex text-yellow-400">
                    {"★".repeat(5)}
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  App Store<br />Rating
                </div>
              </div>
              <div className="flex items-center">
                <div className="mr-2">
                  <div className="text-2xl font-bold text-gray-900">4.8</div>
                  <div className="flex text-yellow-400">
                    {"★".repeat(5)}
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  Play Store<br />Rating
                </div>
              </div>
            </div>

            <div className="space-x-4">
              <Button size="lg" className="bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700" asChild>
                <Link to="/pricing">Start Streaming</Link>
              </Button>
              <Button size="lg" variant="outline" className="text-gray-700 border-gray-300 hover:bg-gray-50" asChild>
                <Link to="/pricing">View Plans</Link>
              </Button>
            </div>

            {/* Partner logos */}
            <div className="mt-12">
              <p className="text-sm text-gray-500 mb-4">Trusted by creators on</p>
              <div className="flex flex-wrap gap-8 items-center justify-center lg:justify-start">
                <img src="/youtube-logo.svg" alt="YouTube" className="h-6 opacity-50 hover:opacity-75 transition-opacity" />
                <img src="/twitch-logo.svg" alt="Twitch" className="h-6 opacity-50 hover:opacity-75 transition-opacity" />
                <img src="/facebook-logo.svg" alt="Facebook" className="h-6 opacity-50 hover:opacity-75 transition-opacity" />
              </div>
            </div>
          </div>

          {/* Video showcase */}
          <div className="hidden lg:block relative">
            <div className="relative z-10">
              <div className="w-full max-w-[800px] mx-auto rounded-2xl shadow-2xl overflow-hidden">
                <video 
                  className="w-full h-full object-cover"
                  autoPlay 
                  loop 
                  muted 
                  playsInline
                >
                  <source src="/assets/kawaii.mp4" type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>
            {/* Decorative elements */}
            <div className="absolute top-1/2 right-0 w-72 h-72 bg-purple-200/50 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2"></div>
            <div className="absolute bottom-0 left-1/2 w-72 h-72 bg-pink-200/50 rounded-full blur-3xl transform -translate-x-1/2 translate-y-1/4"></div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Multi-Platform Streaming</h3>
            <p className="text-gray-600">
              Stream to multiple platforms simultaneously and reach a wider audience.
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Guest Management</h3>
            <p className="text-gray-600">
              Invite guests to your stream with just a link. No downloads required.
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Professional Tools</h3>
            <p className="text-gray-600">
              Brand your stream with custom overlays, backgrounds, and graphics.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-32 py-12 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">About</h3>
              <p className="text-gray-600">
                Spreadify AI is a professional live streaming platform that helps content creators reach wider audiences.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Legal</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/privacy-policy" className="text-gray-600 hover:text-purple-600">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="text-gray-600 hover:text-purple-600">
                    Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Support</h3>
              <ul className="space-y-2">
                <li>
                  <a href="mailto:support@spreadify.ai" className="text-gray-600 hover:text-purple-600">
                    Contact Us
                  </a>
                </li>
                <li>
                  <Link to="/faq" className="text-gray-600 hover:text-purple-600">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Connect</h3>
              <div className="flex space-x-4">
                <a href="https://twitter.com/spreadifyai" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-purple-600">
                  Twitter
                </a>
                <a href="https://linkedin.com/company/spreadifyai" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-purple-600">
                  LinkedIn
                </a>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-200">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-600">© 2024 Spreadify AI. All rights reserved.</p>
              <div className="mt-4 md:mt-0">
                <Link to="/privacy-policy" className="text-gray-600 hover:text-purple-600">
                  Privacy Policy
                </Link>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
