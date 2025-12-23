import {Component, input} from '@angular/core';

@Component({
  selector: 'app-header-modal',
  imports: [],
  templateUrl: './header-modal.component.html',
  standalone: true,
  styleUrl: './header-modal.component.scss'
})
export class HeaderModalComponent {
  public classModal = input<string>('');
}
