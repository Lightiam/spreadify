import * as React from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { toast } from "sonner";
import { payments } from "../../lib/api";
import { PayPalButtons } from "@paypal/react-paypal-js";

interface DonateDialogProps {
  channelId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DonateDialog({
  channelId: _channelId,
  open,
  onOpenChange,
}: DonateDialogProps) {
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [amount, setAmount] = React.useState("");
  const [message, setMessage] = React.useState("");

  const handleDonate = async () => {
    const amountValue = parseFloat(amount);
    if (!amountValue || amountValue <= 0) {
      toast("Please enter a valid amount");
      return;
    }

    setIsProcessing(true);
    try {
      await payments.createPaymentIntent(amountValue * 100);
      toast("Donation sent successfully");
      onOpenChange(false);
      setAmount("");
      setMessage("");
    } catch (error) {
      toast("Failed to process donation");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Support this Channel</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Amount ($)</label>
            <Input
              type="number"
              min="1"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Enter amount"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Message (Optional)</label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Add a message of support"
              maxLength={200}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {message.length}/200 characters
            </p>
          </div>
          <div className="space-y-4">
            <Button
              className="w-full"
              onClick={handleDonate}
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Donate with Card"}
            </Button>
            
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Or pay with
                </span>
              </div>
            </div>

            <PayPalButtons
              createOrder={async () => {
                try {
                  const response = await payments.createPayPalOrder(parseFloat(amount));
                  return response.data.id;
                } catch (error) {
                  toast({
                    title: "Error",
                    description: "Failed to create PayPal order",
                    variant: "destructive",
                  });
                  throw error;
                }
              }}
              onApprove={async (data) => {
                try {
                  await payments.capturePayPalOrder(data.orderID);
                  toast("Donation successful!");
                  onOpenChange(false);
                } catch (error) {
                  toast({
                    title: "Error",
                    description: "Failed to process PayPal payment",
                    variant: "destructive",
                  });
                }
              }}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
