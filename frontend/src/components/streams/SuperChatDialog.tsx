import * as React from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { toast } from "sonner";
import { payments } from "../../lib/api";

interface SuperChatDialogProps {
  streamId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SuperChatDialog({
  streamId,
  open,
  onOpenChange,
}: SuperChatDialogProps) {
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [amount, setAmount] = React.useState("");
  const [message, setMessage] = React.useState("");

  const handleSuperChat = async () => {
    const amountValue = parseFloat(amount);
    if (!amountValue || amountValue <= 0 || !message) {
      toast({
        description: "Please enter a valid amount and message",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);
    try {
      await payments.createPaymentIntent(amountValue * 100);
      await payments.processSuperChat(streamId, amountValue * 100, message);
      toast({
        description: "Super Chat sent successfully"
      });
      onOpenChange(false);
      setAmount("");
      setMessage("");
    } catch (error) {
      toast({
        description: "Failed to send Super Chat",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send Super Chat</DialogTitle>
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
            <label className="text-sm font-medium">Message</label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter your message"
              maxLength={200}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {message.length}/200 characters
            </p>
          </div>
          <Button
            className="w-full"
            onClick={handleSuperChat}
            disabled={isProcessing}
          >
            {isProcessing ? "Processing..." : "Send Super Chat"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
