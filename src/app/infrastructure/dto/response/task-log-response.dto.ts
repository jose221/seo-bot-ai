export interface TaskLogEntryResponseDto {
  id: string;
  level: string;
  message: string;
  progress_percentage: number | null;
  created_at: string;
}

export interface TaskLogListResponseDto {
  task_type: string;
  task_id: string;
  items: TaskLogEntryResponseDto[];
}
