import type { Newsletter } from '../types/newsletter';

// API base URL - adjust based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// TODO: Substituir por chamadas reais da API quando o backend estiver pronto
const mockNewsletters: Newsletter[] = [
  {
    id: '1',
    title: 'AI-generated newsletter title',
    createdAt: '2024-11-05 14:30',
    status: 'draft',
  },
  {
    id: '2',
    title: 'AI-generated newsletter title',
    createdAt: '2024-11-04 10:15',
    status: 'published',
  },
  {
    id: '3',
    title: 'AI-generated newsletter title',
    createdAt: '2024-11-03 09:00',
    status: 'published',
  },
  {
    id: '4',
    title: 'AI-generated newsletter title',
    createdAt: '2024-11-02 16:20',
    status: 'published',
  },
  {
    id: '5',
    title: 'AI-generated newsletter title',
    createdAt: '2024-11-01 08:45',
    status: 'published',
  },
];

export const apiService = {
  async getNewsletters(): Promise<Newsletter[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/newsletter/list`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch newsletters');
      }
      
      const data = await response.json();
      
      // Mapear os dados do backend para o formato do frontend
      return data.newsletters.map((item: any) => ({
        id: String(item.id),
        title: item.topic,
        createdAt: item.created_on,
        status: 'published', // Backend não tem status, definir como published
      }));
    } catch (error) {
      console.error('Error fetching newsletters:', error);
      throw error;
    }
  },

  async createNewsletter(topic: string, htmlContent: string): Promise<Newsletter> {
    try {
      const response = await fetch(`${API_BASE_URL}/newsletter/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic,
          html_content: htmlContent,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save newsletter');
      }

      const data = await response.json();

      return {
        id: String(data.id),
        title: topic,
        createdAt: new Date().toISOString(),
        status: 'published',
      };
    } catch (error) {
      console.error('Error creating newsletter:', error);
      throw error;
    }
  },

  async exportNewsletterPDF(newsletterId: string): Promise<Blob> {
    try {
      const response = await fetch(`${API_BASE_URL}/newsletter/${newsletterId}/export-pdf`);
      
      if (!response.ok) {
        throw new Error('Failed to export newsletter as PDF');
      }
      
      return await response.blob();
    } catch (error) {
      console.error('Error exporting newsletter as PDF:', error);
      throw error;
    }
  },

  async exportMultipleNewslettersPDF(newsletterIds: string[]): Promise<void> {
    for (const id of newsletterIds) {
      try {
        const blob = await this.exportNewsletterPDF(id);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `newsletter_${id}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        // Small delay between downloads to avoid browser blocking
        if (newsletterIds.length > 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      } catch (error) {
        console.error(`Failed to export newsletter ${id}:`, error);
        throw error;
      }
    }
  },

  async generateNewsletter(topic: string, query: string, language: string): Promise<{
    html_content: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/newsletter/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        newsletter_topic: topic,
        query: query,
        language: language 
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to generate newsletter');
    }
    
    return response.json();
  },

  // ============================================================================
  // PDF Upload/Processing APIs
  // ============================================================================

  async uploadPDFs(items: Array<{ url: string; filename?: string }>): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/etl/pdf-upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to upload PDFs');
    }
    
    return response.json();
  },

  async runPDFProcessing(): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/etl/run`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to run PDF processing');
    }
    
    return response.json();
  },

  async getPDFJobStatus(jobId: string): Promise<{ job_id: string; status: string; detail: string | null }> {
    const response = await fetch(`${API_BASE_URL}/etl/pdf-job-status/${jobId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get PDF job status');
    }
    
    const data = await response.json();
    
    // Backend retorna: "queued", "downloading", "saved", "ingesting", "done", "error"
    return {
      job_id: data.job_id,
      status: data.status,
      detail: data.detail
    };
  },

  // ============================================================================
  // IBGE Table APIs
  // ============================================================================

  async uploadIBGEData(dataSources: Array<{ url: string; table_name: string }>): Promise<{
    message: string;
    total: number;
    jobs: Array<{ job_id: string; table_name: string; url: string; status: string }>;
  }> {
    const response = await fetch(`${API_BASE_URL}/etl/upload_data_ibge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data_sources: dataSources }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to upload IBGE data');
    }
    
    return response.json();
  },

  async getIBGEJobStatus(jobId: string): Promise<{
    job_id: string;
    status: string;
    message: string;
    table_name: string;
    url: string;
    result?: any;
  }> {
    const response = await fetch(`${API_BASE_URL}/etl/ibge-job-status/${jobId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get IBGE job status');
    }
    
    const data = await response.json();
    
    // Backend retorna: "pending", "processing", "completed", "failed"
    return {
      job_id: data.job_id,
      status: data.status,
      message: data.message,
      table_name: data.table_name,
      url: data.url,
      result: data.result
    };
  },

  async deleteDataSource(tableName: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/etl/data_sources/${tableName}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete data source');
    }
    
    return response.json();
  },
};
