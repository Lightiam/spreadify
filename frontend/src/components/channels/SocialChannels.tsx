import React, { useState, useEffect } from 'react';
import './SocialChannels.css';
import { FaFacebook, FaTwitter, FaInstagram, FaLinkedin, FaYoutube } from 'react-icons/fa';
import { api } from '../../lib/api';
import { toast } from 'sonner';

interface SocialChannel {
  id: string;
  platform: string;
  link: string;
}

interface SocialChannelsProps {
  channelId: string;
}

const SocialChannels: React.FC<SocialChannelsProps> = ({ channelId }) => {
  const [channels, setChannels] = useState<SocialChannel[]>([]);
  const [newChannel, setNewChannel] = useState({ platform: '', link: '' });

  const platforms = [
    { name: 'Facebook', icon: <FaFacebook /> },
    { name: 'Twitter', icon: <FaTwitter /> },
    { name: 'Instagram', icon: <FaInstagram /> },
    { name: 'LinkedIn', icon: <FaLinkedin /> },
    { name: 'YouTube', icon: <FaYoutube /> },
  ];

  useEffect(() => {
    loadSocialChannels();
  }, [channelId]);

  const loadSocialChannels = async () => {
    try {
      const response = await api.get(`/channels/${channelId}/social-channels`);
      setChannels(response.data);
    } catch (error) {
      toast.error("Failed to load social channels");
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setNewChannel({ ...newChannel, [name]: value });
  };

  const addChannel = async () => {
    if (newChannel.platform && newChannel.link) {
      try {
        const response = await api.post(`/channels/${channelId}/social-channels`, newChannel);
        setChannels([...channels, response.data]);
        setNewChannel({ platform: '', link: '' });
        toast.success("Social channel added successfully");
      } catch (error) {
        toast.error("Failed to add social channel");
      }
    }
  };

  const removeChannel = async (socialChannelId: string) => {
    try {
      await api.delete(`/channels/social-channels/${socialChannelId}`);
      setChannels(channels.filter(channel => channel.id !== socialChannelId));
      toast.success("Social channel removed successfully");
    } catch (error) {
      toast.error("Failed to remove social channel");
    }
  };

  return (
    <div className="social-channels-container">
      <div className="add-channel-form">
        <select
          name="platform"
          value={newChannel.platform}
          onChange={handleInputChange}
          required
        >
          <option value="" disabled>Select Platform</option>
          {platforms.map((platform, index) => (
            <option key={index} value={platform.name}>
              {platform.name}
            </option>
          ))}
        </select>
        <input
          type="url"
          name="link"
          placeholder="Enter profile link"
          value={newChannel.link}
          onChange={handleInputChange}
          required
        />
        <button onClick={addChannel}>Add Channel</button>
      </div>

      <div className="channels-list">
        {channels.map((channel) => {
          const platform = platforms.find((p) => p.name === channel.platform);
          return (
            <div key={channel.id} className="channel-item">
              <span className="channel-icon">{platform?.icon}</span>
              <a href={channel.link} target="_blank" rel="noopener noreferrer">
                {channel.platform}
              </a>
              <button onClick={() => removeChannel(channel.id)}>Remove</button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SocialChannels;
