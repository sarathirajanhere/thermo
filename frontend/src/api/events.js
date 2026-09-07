import axios from 'axios';
import fallbackEvents from '../data/mockEvents.json';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function fetchEvents() {
  try {
    const response = await axios.get(`${API_BASE_URL}/events`, { timeout: 2000 });
    return response.data;
  } catch (error) {
    console.warn('Backend unavailable. Using local fallback demo data.', error);
    return fallbackEvents;
  }
}