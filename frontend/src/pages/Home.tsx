// No React import needed
import { Button } from "../components/ui/button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <h1 className="text-2xl font-bold">Spreadify</h1>
          <div className="flex gap-4">
            {user ? (
              <Button onClick={() => navigate("/dashboard")}>Dashboard</Button>
            ) : (
              <>
                <Button variant="ghost" onClick={() => navigate("/login")}>
                  Login
                </Button>
                <Button onClick={() => navigate("/register")}>Get Started</Button>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1">
        <section className="container mx-auto px-4 py-24 text-center">
          <h2 className="mb-4 text-4xl font-bold">Stream to Multiple Platforms</h2>
          <p className="mb-8 text-xl text-muted-foreground">
            Reach your audience everywhere with one click
          </p>
          <Button size="lg" onClick={() => navigate(user ? "/dashboard" : "/register")}>
            Start Streaming Now
          </Button>
        </section>
        <section className="bg-muted py-24">
          <div className="container mx-auto px-4">
            <h3 className="mb-12 text-center text-3xl font-bold">
              Key Features
            </h3>
            <div className="grid gap-8 md:grid-cols-3">
              <div className="rounded-lg bg-background p-6">
                <h4 className="mb-2 text-xl font-semibold">Multi-Platform</h4>
                <p className="text-muted-foreground">
                  Stream to YouTube, Facebook, Twitch, and more simultaneously
                </p>
              </div>
              <div className="rounded-lg bg-background p-6">
                <h4 className="mb-2 text-xl font-semibold">Live Chat</h4>
                <p className="text-muted-foreground">
                  Engage with your audience across all platforms in one place
                </p>
              </div>
              <div className="rounded-lg bg-background p-6">
                <h4 className="mb-2 text-xl font-semibold">Analytics</h4>
                <p className="text-muted-foreground">
                  Track your performance and grow your audience
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
