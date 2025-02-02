import * as React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { auth } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { toast } from "sonner";

export function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken, setUser } = useAuth();

  React.useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      if (!code) {
        toast({
          title: "Error",
          description: "Authentication failed",
          variant: "destructive",
        });
        navigate("/login");
        return;
      }

      try {
        const provider = window.location.pathname.split("/").pop();
        let response;
        
        switch (provider) {
          // Only Facebook and Twitter social logins are supported
          case "facebook":
            response = await auth.getFacebookCallback(code);
            break;
          case "twitter":
            response = await auth.getTwitterCallback(code);
            break;
          default:
            throw new Error("Unknown provider");
        }
        
        setToken(response.data.access_token);
        const userResponse = await auth.me();
        setUser(userResponse.data);
        navigate("/dashboard");
      } catch (error) {
        toast({
          title: "Error",
          description: "Authentication failed",
          variant: "destructive",
        });
        navigate("/login");
      }
    };

    handleCallback();
  }, [searchParams, navigate, setToken, setUser, toast]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Authenticating...</h2>
        <p className="text-muted-foreground">Please wait while we log you in</p>
      </div>
    </div>
  );
}
