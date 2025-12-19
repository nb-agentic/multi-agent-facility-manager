import React from 'react';
import './EventLog.css';

interface EventLogProps {
  events: any[];
}

const EventLog: React.FC<EventLogProps> = ({ events }) => {
  return (
    <div className="event-log-container">
      <h2>Event Log</h2>
      <div className="log-box">
        {events.map((event, index) => (
          <pre key={index} className="log-entry">
            {JSON.stringify(event, null, 2)}
          </pre>
        ))}
      </div>
    </div>
  );
};

export default EventLog;