import {numberToArray} from '@/app/helper/map-data.helper';


export class PaginatorHelper<T> {
  public all: T[];
  public pageSize: number;
  private currentPage: number;

  constructor(data: T[], pageSize: number) {
    this.all = data ?? [];
    this.pageSize = pageSize;
    this.currentPage = 1;
  }
  reformatData(pageSize: number, data: T[] = this.all ): void {
    this.all = data ?? [];
    this.pageSize = pageSize;
    this.currentPage = 1;
  }
  getCurrentPageData(): T[] {
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return Array.isArray(this.all) ? this.all.slice(startIndex, endIndex) : [];
  }
  public get data(): T[] {
    return this.getCurrentPageData();
  }

  goToPage(pageNumber: number): void {
    if (pageNumber >= 1 && pageNumber <= this.getTotalPages) {
      this.currentPage = pageNumber;
    }
  }

  nextPage(): void {
    if (this.currentPage < this.getTotalPages) {
      this.currentPage++;
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }

  public get getTotalPages(): number {
    return Math.ceil(this.all.length / this.pageSize);
  }
  public get getCurrentPage(): number {
    return this.currentPage;
  }

  public get getTotalIndex(): number {
    return this.all.length;
  }

  get getVisibleRange(): { start: number; end: number } {
    const start = (this.currentPage - 1) * this.pageSize + 1;
    const end = Math.min(start + this.pageSize - 1, this.data.length);
    return { start, end };
  }

  get getVisibleStartIndex(): number {
    return (this.currentPage - 1) * this.pageSize + 1;
  }

  get getVisibleEndIndex(): number {
    const endIndex = this.getVisibleStartIndex + this.pageSize - 1;
    return this.getVisibleStartIndex + Math.min(endIndex, this.data.length) -1;
  }

  get getPaginatedData(): T[][] {
    let page = [];

    // The matrix that will contain all the pages
    let paginatedMatrix = [];

    // Iterate through the original array and group by page size
    for (let i = 0; i < this.all.length; i++) {
      page.push(this.all[i]);

      // Check if the page is full or if it's the last element of the array
      if (page.length === this.pageSize || i === this.all.length - 1) {
        paginatedMatrix.push(page);
        page = []; // Reset the page for the next elements
      }
    }

    return paginatedMatrix;
  }

  listPagination(sizeArray: number){
    let list: number[] = []
    let init = this.getCurrentPage;
    let finish =  this.getTotalPages;

    if((!list.find(item => item == 1)) && init != 1){
      list = list.concat([1])
    }

    if(init == finish || (init + sizeArray) >= finish){
      init = (init - sizeArray) + 1;
    }

    list = list.concat(numberToArray(sizeArray, init))

    if(!list.find(item => item == finish)){
      list = list.concat([finish])
    }
    return [...new Set(list)];
  }

}
