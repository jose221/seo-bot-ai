import {Component, input, ViewEncapsulation} from '@angular/core';

@Component({
  selector: 'app-default-modal',
  imports: [],
  templateUrl: './default-modal.html',
  styleUrl: './default-modal.scss',
  encapsulation: ViewEncapsulation.None
})
export class DefaultModal {
  expanded = input<boolean>(true);
  classModalDialog = input<string>('');
}
