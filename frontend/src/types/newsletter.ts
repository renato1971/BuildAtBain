export type NewsletterStatus = 'draft' | 'published';

export interface Newsletter {
  id: string;
  title: string;
  createdAt: string;
  status: NewsletterStatus;
}
