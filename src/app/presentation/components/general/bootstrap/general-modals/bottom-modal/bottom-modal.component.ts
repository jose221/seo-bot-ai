import {Component, Input} from '@angular/core';

@Component({
  selector: 'app-bottom-modal',
  imports: [
  ],
  templateUrl: './bottom-modal.component.html',
  standalone: true,
  styleUrl: './bottom-modal.component.scss'
})
export class BottomModalComponent {
  @Input() expanded: boolean = true
}
