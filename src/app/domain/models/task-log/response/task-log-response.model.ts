export class TaskLogEntryResponseModel {
  constructor(
    public id: string,
    public level: string,
    public message: string,
    public progress_percentage: number | null,
    public created_at: string,
  ) {}
}

export class TaskLogListResponseModel {
  constructor(
    public task_type: string,
    public task_id: string,
    public items: TaskLogEntryResponseModel[],
  ) {}
}
