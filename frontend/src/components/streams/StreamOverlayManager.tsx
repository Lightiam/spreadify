import * as React from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { toast } from "sonner";
import { Trash2, Move } from "lucide-react";

interface StreamOverlayManagerProps {
  streamId: string;
  onOverlayChange?: () => void;
}

interface Overlay {
  id: string;
  path: string;
  position_x: number;
  position_y: number;
  scale: number;
  active: boolean;
}

export function StreamOverlayManager({ streamId, onOverlayChange }: StreamOverlayManagerProps) {
  const [overlays, setOverlays] = React.useState<Overlay[]>([]);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });
  const [scale, setScale] = React.useState(100);
  const [isUploading, setIsUploading] = React.useState(false);

  const fetchOverlays = React.useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/overlays/${streamId}`);
      if (!response.ok) throw new Error("Failed to fetch overlays");
      const data = await response.json();
      setOverlays(data);
    } catch (error) {
      console.error("Error fetching overlays:", error);
      toast({
        title: "Error",
        description: "Failed to load overlays",
        variant: "destructive",
      });
    }
  }, [streamId]);

  React.useEffect(() => {
    fetchOverlays();
  }, [fetchOverlays]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!["image/png", "image/jpeg", "image/gif"].includes(file.type)) {
        toast({
          title: "Invalid file type",
          description: "Please upload a PNG, JPEG, or GIF image",
          variant: "destructive",
        });
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("position_x", position.x.toString());
    formData.append("position_y", position.y.toString());
    formData.append("scale", scale.toString());

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/overlays/${streamId}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to upload overlay");

      await fetchOverlays();
      onOverlayChange?.();
      setSelectedFile(null);
      setPosition({ x: 0, y: 0 });
      setScale(100);

      toast({
        title: "Success",
        description: "Overlay uploaded successfully",
      });
    } catch (error) {
      console.error("Error uploading overlay:", error);
      toast({
        title: "Error",
        description: "Failed to upload overlay",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUpdateOverlay = async (overlayId: string, updates: Partial<Overlay>) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/overlays/${overlayId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error("Failed to update overlay");

      await fetchOverlays();
      onOverlayChange?.();
      
      toast({
        title: "Success",
        description: "Overlay updated successfully",
      });
    } catch (error) {
      console.error("Error updating overlay:", error);
      toast({
        title: "Error",
        description: "Failed to update overlay",
        variant: "destructive",
      });
    }
  };

  const handleDeleteOverlay = async (overlayId: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/overlays/${overlayId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete overlay");

      await fetchOverlays();
      onOverlayChange?.();
      
      toast({
        title: "Success",
        description: "Overlay deleted successfully",
      });
    } catch (error) {
      console.error("Error deleting overlay:", error);
      toast({
        title: "Error",
        description: "Failed to delete overlay",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="overlay">Upload Overlay</Label>
          <Input
            id="overlay"
            type="file"
            accept="image/png,image/jpeg,image/gif"
            onChange={handleFileChange}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="position-x">X Position</Label>
            <Input
              id="position-x"
              type="number"
              value={position.x}
              onChange={(e) => setPosition({ ...position, x: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div>
            <Label htmlFor="position-y">Y Position</Label>
            <Input
              id="position-y"
              type="number"
              value={position.y}
              onChange={(e) => setPosition({ ...position, y: parseInt(e.target.value) || 0 })}
            />
          </div>
        </div>
        <div>
          <Label htmlFor="scale">Scale (%)</Label>
          <Input
            id="scale"
            type="number"
            min="1"
            max="500"
            value={scale}
            onChange={(e) => setScale(parseInt(e.target.value) || 100)}
          />
        </div>
        <Button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
        >
          {isUploading ? "Uploading..." : "Upload Overlay"}
        </Button>
      </div>

      <div className="space-y-4">
        <h3 className="font-medium">Active Overlays</h3>
        {overlays.length === 0 ? (
          <p className="text-sm text-muted-foreground">No overlays added yet</p>
        ) : (
          <div className="space-y-4">
            {overlays.map((overlay) => (
              <div
                key={overlay.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <img
                    src={overlay.path}
                    alt=""
                    className="w-16 h-16 object-cover rounded"
                  />
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Move className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        Position: ({overlay.position_x}, {overlay.position_y})
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Scale: {overlay.scale}%
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleUpdateOverlay(overlay.id, { active: !overlay.active })}
                  >
                    {overlay.active ? "Hide" : "Show"}
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteOverlay(overlay.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
