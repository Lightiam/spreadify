import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-full aspect-square max-w-2xl bg-gradient-to-b from-brand-50 via-brand-50/50 to-transparent -z-10 rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/4 opacity-75"></div>
        <div className="absolute bottom-0 left-0 w-full aspect-square max-w-2xl bg-gradient-to-t from-brand-50 via-brand-50/50 to-transparent -z-10 rounded-full blur-3xl transform -translate-x-1/3 translate-y-1/4 opacity-75"></div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <nav className="flex justify-between items-center py-6 mb-16">
          <div className="flex items-center space-x-8">
            <div className="text-2xl font-bold text-brand-600">
              Spreadify A
            </div>
            <div className="hidden md:flex space-x-6">
              <Link to="/features" className="text-gray-600 hover:text-brand-600 transition-colors">Features</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-brand-600 transition-colors">Pricing</Link>
              <Link to="/docs" className="text-gray-600 hover:text-brand-600 transition-colors">Documentation</Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              className="text-gray-700 hover:text-brand-600 hover:bg-brand-50/50 transition-all"
              asChild
            >
              <Link to="/login">Sign In</Link>
            </Button>
            <Button 
              variant="brand"
              className="shadow-md hover:shadow-brand-200/50 transition-all"
              asChild
            >
              <Link to="/login">Get Started</Link>
            </Button>
          </div>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center py-16">
          <div className="text-center lg:text-left">
            <h1 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Meet Spreadify A
              <span className="block mt-4 bg-gradient-to-r from-brand-600 via-brand-500 to-brand-700 bg-clip-text text-transparent animate-gradient">On-brand Streaming Wherever You Create</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Elevate your live streaming with professional multi-platform broadcasting.
              Connect with your audience across all major platforms seamlessly.
            </p>
            
            {/* Ratings and social proof */}
            <div className="flex flex-wrap gap-8 mb-8">
              <div className="flex items-center">
                <div className="mr-2">
                  <div className="text-2xl font-bold text-gray-900">4.9</div>
                  <div className="flex text-brand-500">
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
                  <div className="flex text-brand-500">
                    {"★".repeat(5)}
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  Play Store<br />Rating
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto lg:mx-0">
              <Button 
                variant="brand" 
                size="xl" 
                className="w-full sm:w-auto font-semibold shadow-lg hover:shadow-brand-200/50 transition-all" 
                asChild
              >
                <Link to="/login">Get Started</Link>
              </Button>
              <Button 
                variant="outline" 
                size="xl" 
                className="w-full sm:w-auto font-semibold hover:bg-brand-50/50 hover:border-brand-200 transition-all" 
                asChild
              >
                <Link to="/studio">View Demo</Link>
              </Button>
            </div>

            {/* Platform Support */}
            <div className="mt-12">
              <p className="text-sm font-medium text-gray-500 mb-4">Stream directly to</p>
              <div className="flex items-center gap-6">
                <img src="/youtube-logo.svg" alt="YouTube" className="h-5 opacity-60 hover:opacity-100 transition-opacity" />
                <img src="/twitch-logo.svg" alt="Twitch" className="h-5 opacity-60 hover:opacity-100 transition-opacity" />
                <img src="/facebook-logo.svg" alt="Facebook" className="h-5 opacity-60 hover:opacity-100 transition-opacity" />
              </div>
            </div>
          </div>

          {/* Video showcase */}
          <div className="hidden lg:block relative">
            <div className="relative z-10">
              <div className="w-full max-w-4xl mx-auto rounded-xl overflow-hidden bg-gradient-to-br from-brand-50 to-brand-100 p-1 shadow-lg">
                <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-white">
                  <video 
                    key="showcase-video"
                    className="w-full h-full object-cover"
                    autoPlay 
                    loop 
                    muted 
                    playsInline
                    preload="auto"
                  >
                    <source src="/assets/kawaii.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-300 video-loading">
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                      <p className="text-white text-sm font-medium">Loading preview...</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-32 max-w-5xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-brand-600 via-brand-500 to-brand-700 bg-clip-text text-transparent inline-block">
              Everything you need for professional streaming
            </h2>
            <p className="mt-4 text-gray-600 max-w-2xl mx-auto">
              Powerful features designed to help you create professional live streams with ease
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="group p-6 rounded-xl bg-gradient-to-b from-brand-50 to-white border border-brand-100 hover:shadow-lg transition-all hover:border-brand-200">
              <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center mb-4 group-hover:bg-brand-200 transition-colors">
                <svg className="w-6 h-6 text-brand-600 group-hover:text-brand-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900 group-hover:text-brand-600 transition-colors">Multi-Platform Streaming</h3>
              <p className="text-gray-600">
                Stream simultaneously to YouTube, Twitch, and Facebook Live with just one click.
              </p>
            </div>

            <div className="group p-6 rounded-xl bg-gradient-to-b from-brand-50 to-white border border-brand-100 hover:shadow-lg transition-all hover:border-brand-200">
              <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center mb-4 group-hover:bg-brand-200 transition-colors">
                <svg className="w-6 h-6 text-brand-600 group-hover:text-brand-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900 group-hover:text-brand-600 transition-colors">Easy Guest Management</h3>
              <p className="text-gray-600">
                Invite guests with a simple link. No downloads or complex setup needed.
              </p>
            </div>

            <div className="group p-6 rounded-xl bg-gradient-to-b from-brand-50 to-white border border-brand-100 hover:shadow-lg transition-all hover:border-brand-200">
              <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center mb-4 group-hover:bg-brand-200 transition-colors">
                <svg className="w-6 h-6 text-brand-600 group-hover:text-brand-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900 group-hover:text-brand-600 transition-colors">Professional Branding</h3>
              <p className="text-gray-600">
                Customize your stream with branded overlays, logos, and themes.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-32 py-12 bg-gradient-to-b from-white to-brand-50/30">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <div className="flex flex-col items-center space-y-6">
              <div className="flex items-center space-x-2">
                <span className="text-xl font-semibold bg-gradient-to-r from-brand-600 via-brand-500 to-brand-700 bg-clip-text text-transparent">Spreadify A</span>
              </div>
              <div className="flex items-center space-x-6">
                <Link to="/privacy-policy" className="text-sm text-gray-600 hover:text-brand-600 transition-colors">
                  Privacy Policy
                </Link>
                <Link to="/terms" className="text-sm text-gray-600 hover:text-brand-600 transition-colors">
                  Terms of Service
                </Link>
                <a href="mailto:support@spreadify.app" className="text-sm text-gray-600 hover:text-brand-600 transition-colors">
                  Contact Support
                </a>
              </div>
              <div className="text-sm text-gray-500">
                © {new Date().getFullYear()} Spreadify A. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
