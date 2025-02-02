import * as React from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { toast } from "sonner";
import { streams } from "../../lib/api";

interface ScheduleStreamDialogProps {
  channelId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onScheduled: () => void;
}

export function ScheduleStreamDialog({
  channelId,
  open,
  onOpenChange,
  onScheduled,
}: ScheduleStreamDialogProps) {
  const [isScheduling, setIsScheduling] = React.useState(false);
  const [streamData, setStreamData] = React.useState({
    title: "",
    description: "",
    scheduledFor: "",
  });

  const handleSchedule = async () => {
    if (!streamData.title || !streamData.scheduledFor) {
      toast({
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    setIsScheduling(true);
    try {
      await streams.schedule(channelId, streamData);
      toast({
        description: "Stream scheduled successfully"
      });
      onScheduled();
      onOpenChange(false);
      setStreamData({ title: "", description: "", scheduledFor: "" });
    } catch (error) {
      toast({
        description: "Failed to schedule stream",
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule Stream</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Title</label>
            <Input
              value={streamData.title}
              onChange={(e) =>
                setStreamData({ ...streamData, title: e.target.value })
              }
              placeholder="Stream Title"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={streamData.description}
              onChange={(e) =>
                setStreamData({ ...streamData, description: e.target.value })
              }
              placeholder="Stream Description"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Date and Time</label>
            <Input
              type="datetime-local"
              value={streamData.scheduledFor}
              onChange={(e) =>
                setStreamData({ ...streamData, scheduledFor: e.target.value })
              }
              min={new Date().toISOString().slice(0, 16)}
            />
          </div>
          <Button
            className="w-full"
            onClick={handleSchedule}
            disabled={isScheduling}
          >
            {isScheduling ? "Scheduling..." : "Schedule Stream"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
