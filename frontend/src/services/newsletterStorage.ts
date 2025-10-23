import type { NewsletterFormData } from '../types/newsletterForm';

const STORAGE_KEY = 'newsletter_draft';

export const newsletterStorage = {
  save: (data: NewsletterFormData) => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  },

  load: (): NewsletterFormData | null => {
    const data = sessionStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : null;
  },

  clear: () => {
    sessionStorage.removeItem(STORAGE_KEY);
  },
};
