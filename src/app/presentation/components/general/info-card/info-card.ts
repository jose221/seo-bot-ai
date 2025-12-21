import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { CurrencyPipe, DatePipe, PercentPipe, DecimalPipe } from '@angular/common';

export type ContentType = 'coin' | 'date' | 'datetime' | 'percentage' | 'progress' | 'int' | 'float';
export type CardColor = 'primary' | 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'dark';

@Component({
  selector: 'app-info-card',
  imports: [CurrencyPipe, DatePipe, PercentPipe, DecimalPipe],
  templateUrl: './info-card.html',
  styleUrl: './info-card.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InfoCard {
  title = input.required<string>();
  content = input.required<string | number | Date>();
  color = input<CardColor>('primary');
  type_content = input<ContentType>('coin');

  protected readonly borderClass = computed(() => `border-left-${this.color()}`);
  protected readonly textColorClass = computed(() => `text-${this.color()}`);

  protected readonly iconClass = computed(() => {
    const iconMap: Record<ContentType, string> = {
      coin: 'fas fa-dollar-sign',
      date: 'fas fa-calendar',
      datetime: 'fas fa-clock',
      percentage: 'fas fa-percentage',
      progress: 'fas fa-tasks',
      int: 'fas fa-hashtag',
      float: 'fas fa-calculator'
    };
    return iconMap[this.type_content()];
  });

  protected readonly numericContent = computed(() => {
    const content = this.content();
    const type = this.type_content();

    switch (type) {
      case 'coin':
      case 'percentage':
      case 'progress':
      case 'int':
      case 'float':
        return typeof content === 'number' ? content : parseFloat(content as string) || 0;
      default:
        return 0;
    }
  });

  protected readonly dateContent = computed(() => {
    const content = this.content();
    return content instanceof Date ? content : new Date(content as string);
  });

  protected readonly formattedNumericContent = computed(() => {
    const content = this.numericContent();
    const type = this.type_content();

    switch (type) {
      case 'coin':
        return content;
      case 'percentage':
        return content / 100;
      case 'progress':
        return content;
      case 'int':
        return Math.floor(content);
      case 'float':
        return content;
      default:
        return content;
    }
  });
}
