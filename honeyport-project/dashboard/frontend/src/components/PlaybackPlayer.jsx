import React, { useState, useEffect, useRef } from 'react';
import { FaPlay, FaPause, FaStop, FaStepForward, FaStepBackward, FaFastForward, FaFastBackward } from 'react-icons/fa';

const PlaybackPlayer = ({ events = [], onEventSelect }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [timeRange, setTimeRange] = useState({ start: null, end: null });
  const intervalRef = useRef(null);

  useEffect(() => {
    if (events.length > 0) {
      const timestamps = events.map(e => new Date(e.timestamp));
      setTimeRange({
        start: new Date(Math.min(...timestamps)),
        end: new Date(Math.max(...timestamps))
      });
    }
  }, [events]);

  useEffect(() => {
    if (isPlaying && currentIndex < events.length - 1) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex(prev => {
          const next = prev + 1;
          if (next >= events.length) {
            setIsPlaying(false);
            return prev;
          }
          return next;
        });
      }, 1000 / playbackSpeed);
    } else {
      clearInterval(intervalRef.current);
    }

    return () => clearInterval(intervalRef.current);
  }, [isPlaying, currentIndex, events.length, playbackSpeed]);

  useEffect(() => {
    if (events[currentIndex] && onEventSelect) {
      onEventSelect(events[currentIndex]);
    }
  }, [currentIndex, events, onEventSelect]);

  const handlePlay = () => {
    if (currentIndex >= events.length - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleStop = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
  };

  const handleStepForward = () => {
    setCurrentIndex(prev => Math.min(prev + 1, events.length - 1));
  };

  const handleStepBackward = () => {
    setCurrentIndex(prev => Math.max(prev - 1, 0));
  };

  const handleSliderChange = (e) => {
    const newIndex = parseInt(e.target.value);
    setCurrentIndex(newIndex);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getEventTypeColor = (eventType) => {
    const colors = {
      'HTTP_REQUEST': '#3b82f6',
      'SSH_CONNECTION': '#ef4444',
      'TCP_CONNECTION': '#10b981',
      'FTP_CONNECTION': '#f59e0b',
      'SMTP_CONNECTION': '#8b5cf6'
    };
    return colors[eventType] || '#6b7280';
  };

  if (events.length === 0) {
    return (
      <div className="playback-player">
        <div className="no-events">
          <p>No events available for playback</p>
        </div>
      </div>
    );
  }

  const currentEvent = events[currentIndex];
  const progress = (currentIndex / (events.length - 1)) * 100;

  return (
    <div className="playback-player">
      <div className="playback-header">
        <h3>Event Playback</h3>
        <div className="playback-info">
          <span>Event {currentIndex + 1} of {events.length}</span>
          {timeRange.start && timeRange.end && (
            <span>
              {timeRange.start.toLocaleDateString()} - {timeRange.end.toLocaleDateString()}
            </span>
          )}
        </div>
      </div>

      <div className="playback-timeline">
        <div className="timeline-slider">
          <input
            type="range"
            min="0"
            max={events.length - 1}
            value={currentIndex}
            onChange={handleSliderChange}
            className="slider"
          />
          <div className="progress-bar" style={{ width: `${progress}%` }}></div>
        </div>
        
        <div className="timeline-labels">
          {timeRange.start && <span>{formatTime(timeRange.start)}</span>}
          {timeRange.end && <span>{formatTime(timeRange.end)}</span>}
        </div>
      </div>

      <div className="playback-controls">
        <div className="control-buttons">
          <button onClick={() => setCurrentIndex(0)} title="Go to start">
            <FaFastBackward />
          </button>
          <button onClick={handleStepBackward} title="Previous event">
            <FaStepBackward />
          </button>
          {isPlaying ? (
            <button onClick={handlePause} className="play-pause" title="Pause">
              <FaPause />
            </button>
          ) : (
            <button onClick={handlePlay} className="play-pause" title="Play">
              <FaPlay />
            </button>
          )}
          <button onClick={handleStepForward} title="Next event">
            <FaStepForward />
          </button>
          <button onClick={() => setCurrentIndex(events.length - 1)} title="Go to end">
            <FaFastForward />
          </button>
          <button onClick={handleStop} title="Stop">
            <FaStop />
          </button>
        </div>

        <div className="speed-control">
          <label>Speed:</label>
          <select 
            value={playbackSpeed} 
            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
          >
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
            <option value={8}>8x</option>
          </select>
        </div>
      </div>

      {currentEvent && (
        <div className="current-event">
          <div className="event-header">
            <span 
              className="event-type"
              style={{ backgroundColor: getEventTypeColor(currentEvent.event_type) }}
            >
              {currentEvent.event_type}
            </span>
            <span className="event-time">{formatTime(currentEvent.timestamp)}</span>
          </div>
          
          <div className="event-details">
            <div className="detail-row">
              <strong>Source:</strong> {currentEvent.source_ip}:{currentEvent.source_port}
            </div>
            <div className="detail-row">
              <strong>Destination:</strong> {currentEvent.dest_ip}:{currentEvent.dest_port}
            </div>
            {currentEvent.metadata && Object.keys(currentEvent.metadata).length > 0 && (
              <div className="detail-row">
                <strong>Details:</strong>
                <div className="metadata">
                  {Object.entries(currentEvent.metadata).map(([key, value]) => (
                    <div key={key} className="metadata-item">
                      <span className="key">{key}:</span>
                      <span className="value">{String(value).substring(0, 100)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .playback-player {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          margin: 20px 0;
        }

        .playback-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 10px;
          border-bottom: 1px solid #e5e7eb;
        }

        .playback-header h3 {
          margin: 0;
          color: #1f2937;
        }

        .playback-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .playback-timeline {
          margin-bottom: 20px;
        }

        .timeline-slider {
          position: relative;
          margin-bottom: 10px;
        }

        .slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: #e5e7eb;
          outline: none;
          -webkit-appearance: none;
        }

        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }

        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }

        .progress-bar {
          position: absolute;
          top: 0;
          left: 0;
          height: 6px;
          background: #3b82f6;
          border-radius: 3px;
          pointer-events: none;
        }

        .timeline-labels {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .playback-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .control-buttons {
          display: flex;
          gap: 8px;
        }

        .control-buttons button {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .control-buttons button:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .play-pause {
          background: #3b82f6 !important;
          color: white !important;
          border-color: #3b82f6 !important;
        }

        .play-pause:hover {
          background: #2563eb !important;
        }

        .speed-control {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.875rem;
        }

        .speed-control select {
          padding: 4px 8px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
        }

        .current-event {
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          padding: 15px;
          background: #f9fafb;
        }

        .event-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .event-type {
          padding: 4px 8px;
          border-radius: 4px;
          color: white;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .event-time {
          font-size: 0.875rem;
          color: #6b7280;
          font-family: monospace;
        }

        .event-details {
          font-size: 0.875rem;
        }

        .detail-row {
          margin-bottom: 8px;
        }

        .detail-row strong {
          color: #374151;
          margin-right: 8px;
        }

        .metadata {
          margin-top: 5px;
          padding-left: 15px;
        }

        .metadata-item {
          margin-bottom: 4px;
          font-family: monospace;
          font-size: 0.8rem;
        }

        .metadata-item .key {
          color: #6b7280;
          margin-right: 8px;
        }

        .metadata-item .value {
          color: #374151;
        }

        .no-events {
          text-align: center;
          padding: 40px;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default PlaybackPlayer;
