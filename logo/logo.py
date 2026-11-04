import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(3.5, 1.4))
plt.text(0, 0, 'p', fontname='ubuntu', fontsize=72, fontweight='bold', color='#009999ff')
plt.text(0.045, 0, 'Area', fontname='ubuntu', fontsize=72, fontweight='bold', color='#b3b3b3ff')
plt.ylim([-0.15, 0.4])
plt.xlim([ 0.0, 0.2])
plt.axis('off')
ax.axes.get_xaxis().set_visible(False)                                         
ax.axes.get_yaxis().set_visible(False)
plt.savefig('logo.png', dpi=200, bbox_inches='tight', pad_inches=0)                                       
