import React, { useState } from 'react';

interface Event {
  id: number;
  title: string;
  date: string;
  time: string;
  description: string;
}

const Schedule: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([
    { id: 1, title: 'Team Meeting', date: '2025-04-28', time: '10:00 AM', description: 'Weekly team sync' },
    { id: 2, title: 'Client Call', date: '2025-04-29', time: '2:00 PM', description: 'Project update call' },
    { id: 3, title: 'Product Demo', date: '2025-04-30', time: '11:00 AM', description: 'New feature demonstration' },
  ]);
  
  const [newEvent, setNewEvent] = useState<Omit<Event, 'id'>>({
    title: '',
    date: '',
    time: '',
    description: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewEvent(prev => ({ ...prev, [name]: value }));
  };

  const handleAddEvent = () => {
    if (newEvent.title && newEvent.date && newEvent.time) {
      const event: Event = {
        id: Date.now(),
        ...newEvent
      };
      setEvents(prev => [...prev, event]);
      setNewEvent({ title: '', date: '', time: '', description: '' });
    }
  };

  const handleDeleteEvent = (id: number) => {
    setEvents(prev => prev.filter(event => event.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Schedule</h2>
        
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Add New Event</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                name="title"
                value={newEvent.title}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Event title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input
                type="date"
                name="date"
                value={newEvent.date}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
              <input
                type="time"
                name="time"
                value={newEvent.time}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                name="description"
                value={newEvent.description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Event description"
                rows={2}
              ></textarea>
            </div>
          </div>
          <button
            onClick={handleAddEvent}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Add Event
          </button>
        </div>
        
        <div>
          <h3 className="text-lg font-medium mb-2">Upcoming Events</h3>
          <div className="space-y-4">
            {events.map(event => (
              <div key={event.id} className="border rounded-md p-4">
                <div className="flex justify-between">
                  <h4 className="font-medium">{event.title}</h4>
                  <button
                    onClick={() => handleDeleteEvent(event.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </div>
                <p className="text-sm text-gray-600">{event.date} at {event.time}</p>
                <p className="mt-2">{event.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Schedule;
