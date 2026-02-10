import matplotlib.pyplot as plt
import numpy as np

# Ваши данные
response_times = [0.415, 0.125, 0.183, 0.593, 0.281, 0.258, 0.358, 0.689, 0.146, 0.115,
         0.155, 0.155, 0.125, 0.152, 0.132, 0.133, 0.097, 0.142, 0.168, 0.198,
         0.211, 0.189, 0.203, 0.176, 0.163, 0.157, 0.142, 0.138, 0.145, 0.151,
         0.148, 0.139, 0.167, 0.154, 0.161, 0.173, 0.182, 0.192, 0.205, 0.188,
         0.196, 0.178, 0.165, 0.172, 0.184, 0.193, 0.201, 0.215, 0.189, 0.376,
         0.392, 0.365, 0.358, 0.341, 0.327, 0.318, 0.305, 0.412, 0.398, 0.385,
         0.371, 0.512, 0.498, 0.485, 0.471, 0.612, 0.598, 0.585, 0.571, 0.432,
         0.418, 0.405, 0.391, 0.289, 0.275, 0.262, 0.248, 0.224, 0.231, 0.218,
         0.204, 0.237, 0.243, 0.229, 0.215, 0.221, 0.227, 0.213, 0.199, 0.205,
         0.211, 0.197, 0.183, 0.267, 0.253, 0.239, 0.225, 0.245, 0.231, 0.217,
         0.203, 0.279, 0.265, 0.251, 0.237, 0.193, 0.199, 0.185, 0.171]
commands = list(range(1, len(response_times) + 1))

# Гистограмма
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.hist(response_times, bins=8, edgecolor='black', alpha=0.7)
plt.axvline(np.mean(response_times), color='red', linestyle='--',
            label=f'Среднее: {np.mean(response_times):.3f} с')
plt.xlabel('Время отклика (секунды)')
plt.ylabel('Количество команд')
plt.title('Гистограмма времени отклика')
plt.legend()
plt.grid(True, alpha=0.3)

# График по порядку выполнения
plt.subplot(1, 2, 2)
plt.plot(commands, response_times, 'bo-', linewidth=1, markersize=4)
plt.axhline(y=np.mean(response_times), color='red', linestyle='--',
            label=f'Среднее: {np.mean(response_times):.3f} с')
plt.fill_between(commands, 0, 0.3, alpha=0.2, color='green',
                 label='Быстрые команды (<0.3 с)')
plt.xlabel('Номер команды')
plt.ylabel('Время отклика (секунды)')
plt.title('Время отклика по командам')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('response_time_analysis.png', dpi=300)
plt.show()

# Статистика
print(f"Среднее время: {np.mean(response_times):.3f} с")
print(f"Медиана: {np.median(response_times):.3f} с")
print(f"Стандартное отклонение: {np.std(response_times):.3f} с")
print(f"Минимум: {np.min(response_times):.3f} с")
print(f"Максимум: {np.max(response_times):.3f} с")
print(f"Команд < 0.3 с: {sum(t < 0.3 for t in response_times)}/{len(response_times)}")