import * as React from "react";
import { Button } from "../ui/button";
import { toast } from "sonner";
import { subscriptions } from "../../lib/api";

interface SubscribeButtonProps {
  channelId: string;
  onSubscriptionChange?: () => void;
}

export function SubscribeButton({
  channelId,
  onSubscriptionChange,
}: SubscribeButtonProps) {
  const [isSubscribed, setIsSubscribed] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const checkSubscription = async () => {
      try {
        const response = await subscriptions.getStatus(channelId);
        setIsSubscribed(response.data.isSubscribed);
      } catch (error) {
        console.error("Error checking subscription status:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkSubscription();
  }, [channelId]);

  const handleSubscribe = async () => {
    setIsLoading(true);
    try {
      if (isSubscribed) {
        await subscriptions.unsubscribe(channelId);
        toast("Unsubscribed from channel");
      } else {
        await subscriptions.subscribe(channelId);
        toast("Subscribed to channel");
      }
      setIsSubscribed(!isSubscribed);
      onSubscriptionChange?.();
    } catch (error) {
      toast("Failed to update subscription");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Button variant="outline" disabled>
        Loading...
      </Button>
    );
  }

  return (
    <Button
      variant={isSubscribed ? "default" : "outline"}
      onClick={handleSubscribe}
      disabled={isLoading}
    >
      {isSubscribed ? "Unsubscribe" : "Subscribe"}
    </Button>
  );
}
