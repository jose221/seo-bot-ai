import {Component, input} from '@angular/core';

@Component({
  selector: 'app-default-modal',
  imports: [],
  templateUrl: './default-modal.html',
  styleUrl: './default-modal.scss',
})
export class DefaultModal {
  expanded = input<boolean>(true);
}
