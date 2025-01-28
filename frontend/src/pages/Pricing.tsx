import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

import { stripePromise } from '@/lib/stripe';

interface PricingTier {
  name: string;
  price: number;
  description: string;
  features: string[];
  buttonText: string;
  popular?: boolean;
  priceId: string;
  annualPrice?: number;
}

const pricingTiers: PricingTier[] = [
  {
    name: 'Free',
    price: 0,
    description: 'Multistreaming at no cost',
    features: [
      'Multistream on 2 channels',
      'Local recordings',
      'Basic graphics',
      'Cross-platform chat',
      'Stream analytics',
      'Live health monitor'
    ],
    buttonText: 'Get started for free',
    priceId: 'free'
  },
  {
    name: 'Standard',
    price: 16,
    annualPrice: 160,
    description: 'Perfect for growing creators',
    features: [
      'Multistream on 3 channels',
      'No watermark in Studio',
      'Unlimited cloud recordings',
      'Guest channels',
      '6 on-screen participants',
      '720p HD resolution'
    ],
    buttonText: 'Choose Standard',
    popular: true,
    priceId: 'price_standard'
  },
  {
    name: 'Professional',
    price: 39,
    annualPrice: 390,
    description: 'For professional streamers',
    features: [
      'Multistream on 5 channels',
      'Split audio/video downloads',
      '2 team seats included',
      'Custom channels',
      '10 on-screen participants',
      '1080p Full HD resolution'
    ],
    buttonText: 'Choose Professional',
    priceId: 'price_professional'
  },
  {
    name: 'Business',
    price: 199,
    annualPrice: 1990,
    description: 'For teams and enterprises',
    features: [
      'Multistream on 8 channels',
      '30-day recording storage',
      'Priority support',
      'SRT ingest',
      'RTMP source',
      'Unlimited team seats'
    ],
    buttonText: 'Choose Business',
    priceId: 'price_business'
  }
];

const PricingCard = ({ tier, billingCycle }: { tier: PricingTier; billingCycle: 'monthly' | 'annual' }) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubscribe = async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          priceId: tier.priceId,
          planType: billingCycle,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const { sessionId } = await response.json();
      const stripe = await stripePromise;
      
      if (!stripe) {
        throw new Error('Stripe failed to initialize');
      }

      const { error } = await stripe.redirectToCheckout({ sessionId });
      
      if (error) {
        throw error;
      }
    } catch (error) {
      console.error('Payment error:', error);
      toast({
        variant: "destructive",
        title: "Payment Error",
        description: error instanceof Error ? error.message : "Failed to process payment. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className={`p-8 bg-[#1A0B4B]/30 backdrop-blur-sm border border-indigo-900/30 ${
      tier.popular ? 'ring-2 ring-indigo-500 shadow-lg shadow-indigo-500/20 scale-105' : ''
    } hover:shadow-2xl hover:shadow-indigo-500/10 hover:border-indigo-800/50 hover:scale-[1.02] transition-all duration-300 group relative overflow-hidden`}>
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/5 via-purple-600/5 to-indigo-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      
      <div className="space-y-8 relative">
        {tier.popular && (
          <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm font-medium px-4 py-1.5 rounded-full inline-block mb-4 shadow-lg shadow-indigo-500/20">
            Most Popular
          </div>
        )}
        <div>
          <h3 className="text-2xl font-bold text-white mb-2">{tier.name}</h3>
          <p className="text-gray-400 text-sm">{tier.description}</p>
        </div>
        
        <div className="flex items-baseline">
          <span className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            ${billingCycle === 'annual' && tier.annualPrice ? (tier.annualPrice / 12).toFixed(0) : tier.price}
          </span>
          {tier.price > 0 && (
            <>
              <span className="ml-2 text-gray-400">/mo</span>
              {billingCycle === 'annual' && (
                <span className="ml-3 text-sm text-indigo-400 bg-indigo-400/10 px-2 py-1 rounded-full">
                  Save ${((tier.price * 12 - tier.annualPrice!) / 12).toFixed(0)}/mo
                </span>
              )}
            </>
          )}
        </div>

        <div className="h-px bg-gradient-to-r from-transparent via-indigo-900/50 to-transparent my-8"></div>
        
        <ul className="space-y-5">
          {tier.features.map((feature, index) => (
            <li key={index} className="flex items-start group/item">
              <svg
                className="w-5 h-5 text-indigo-400 mr-3 mt-0.5 flex-shrink-0 transition-transform duration-300 group-hover/item:scale-110"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span className="text-gray-300 group-hover/item:text-white transition-colors duration-300">{feature}</span>
            </li>
          ))}
        </ul>
        
        <Button
          onClick={handleSubscribe}
          className={`w-full py-6 text-lg font-medium ${
            tier.popular 
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-xl shadow-indigo-500/20' 
              : 'bg-[#1A0B4B] hover:bg-[#240B4B] text-white border border-indigo-800/30'
          } transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/20 hover:scale-[1.02]`}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            tier.buttonText
          )}
        </Button>
      </div>
    </Card>
  );
};

export function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  return (
    <div className="min-h-screen bg-[#0A051E] text-white overflow-hidden">
      <div className="container mx-auto px-4 py-16">
        <div className="relative">
          <div className="absolute inset-0">
            <div className="absolute inset-0 bg-gradient-to-br from-[#1A0B4B] via-[#240B4B] to-[#0A051E] opacity-80"></div>
            <div className="absolute inset-0">
              <div className="w-full h-full overflow-hidden">
                <svg viewBox="0 0 1000 1000" className="w-full h-full opacity-10">
                  <path
                    d="M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500"
                    stroke="url(#blue-gradient)"
                    strokeWidth="1"
                    fill="none"
                    className="animate-draw"
                  >
                    <animate
                      attributeName="d"
                      dur="15s"
                      repeatCount="indefinite"
                      values="M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500;
                             M0,500 C200,600 300,400 500,500 C700,600 800,400 1000,500;
                             M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500"
                    />
                  </path>
                  <path
                    d="M0,520 C200,420 300,620 500,520 C700,420 800,620 1000,520"
                    stroke="url(#purple-gradient)"
                    strokeWidth="1"
                    fill="none"
                    className="animate-draw"
                  >
                    <animate
                      attributeName="d"
                      dur="20s"
                      repeatCount="indefinite"
                      values="M0,520 C200,420 300,620 500,520 C700,420 800,620 1000,520;
                             M0,520 C200,620 300,420 500,520 C700,620 800,420 1000,520;
                             M0,520 C200,420 300,620 500,520 C700,420 800,620 1000,520"
                    />
                  </path>
                  <defs>
                    <linearGradient id="blue-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#4F46E5" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.3" />
                    </linearGradient>
                    <linearGradient id="purple-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#9333EA" stopOpacity="0.3" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>
          <div className="relative text-center mb-16 pt-8">
            <p className="text-sm font-medium text-indigo-400 mb-2">Get started, today</p>
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              Choose how fast you want to grow
            </h1>
            <p className="text-xl text-gray-300 mb-12">
              Create beautiful live streams and broadcast everywhere at once
            </p>
          
          <div className="flex justify-center items-center mt-8 space-x-4">
            <span className={`text-sm ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-400'} transition-colors duration-300`}>
              Monthly
            </span>
            <div 
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
              className={`relative w-20 h-10 rounded-full cursor-pointer transition-colors duration-300 ${
                billingCycle === 'annual' 
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600' 
                  : 'bg-gray-700'
              }`}
            >
              <div 
                className={`absolute top-1 w-8 h-8 rounded-full bg-white transform transition-transform duration-300 ${
                  billingCycle === 'annual' ? 'left-11' : 'left-1'
                }`}
              />
            </div>
            <div className="flex items-center">
              <span className={`text-sm ${billingCycle === 'annual' ? 'text-white' : 'text-gray-400'} transition-colors duration-300`}>
                Annual
              </span>
              <span className="ml-2 text-xs text-indigo-400 bg-indigo-400/10 px-2 py-1 rounded-full">
                (2 months free)
              </span>
            </div>
          </div>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto px-4">
        {pricingTiers.map((tier) => (
          <PricingCard key={tier.name} tier={tier} billingCycle={billingCycle} />
        ))}
      </div>

      <div className="mt-32 text-center relative overflow-hidden rounded-2xl">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-[#1A0B4B]/80 via-[#240B4B]/80 to-[#0A051E]/80"></div>
          <div className="absolute inset-0">
            <svg viewBox="0 0 1000 1000" className="w-full h-full opacity-10 scale-150">
              <path
                d="M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500"
                stroke="url(#enterprise-gradient)"
                strokeWidth="1.5"
                fill="none"
                className="animate-draw"
              >
                <animate
                  attributeName="d"
                  dur="10s"
                  repeatCount="indefinite"
                  values="M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500;
                         M0,500 C200,600 300,400 500,500 C700,600 800,400 1000,500;
                         M0,500 C200,400 300,600 500,500 C700,400 800,600 1000,500"
                />
              </path>
              <defs>
                <linearGradient id="enterprise-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#4F46E5" />
                  <stop offset="100%" stopColor="#9333EA" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
        <div className="relative max-w-4xl mx-auto px-8 py-24">
          <h2 className="text-4xl font-bold mb-6 bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
            Everything for enterprise
          </h2>
          <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
            Customized solutions for media and corporate teams with advanced features and dedicated support
          </p>
          <Button 
            size="lg" 
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white px-12 py-6 text-lg font-medium shadow-xl shadow-indigo-500/20 hover:shadow-2xl hover:shadow-indigo-500/30 hover:scale-[1.02] transition-all duration-300"
          >
            Contact Sales
          </Button>
        </div>
      </div>
      </div>
      </div>
    </div>
  );
}
