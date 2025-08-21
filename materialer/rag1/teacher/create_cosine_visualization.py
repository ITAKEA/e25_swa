import matplotlib.pyplot as plt
import numpy as np

# Set up the figure with 3 subplots
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Cosine Similarity mellem Vektorer', fontsize=16, fontweight='bold')

# Define colors
vector_color1 = '#2E86AB'  # Blue
vector_color2 = '#A23B72'  # Pink
origin_color = '#F18F01'   # Orange

# Case 1: Cosine similarity = 1 (0 degrees)
ax1 = axes[0]
# Two identical vectors
v1 = np.array([1, 0])
v2 = np.array([1, 0])

ax1.quiver(0, 0, v1[0], v1[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color1, width=0.008, label='Vektor u')
ax1.quiver(0, 0, v2[0], v2[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color2, width=0.006, label='Vektor v', alpha=0.7)

ax1.set_xlim(-1.5, 1.5)
ax1.set_ylim(-1.5, 1.5)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)
ax1.set_title('Cosine Similarity = 1\nVinkel = 0°\n"De 2 vektorer er ens"', 
              fontsize=12, pad=20)
ax1.axhline(y=0, color='k', linewidth=0.5)
ax1.axvline(x=0, color='k', linewidth=0.5)

# Calculate cosine similarity
cos_sim_1 = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Case 2: Cosine similarity = 0 (90 degrees)
ax2 = axes[1]
# Two perpendicular vectors
v1 = np.array([1, 0])
v2 = np.array([0, 1])

ax2.quiver(0, 0, v1[0], v1[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color1, width=0.008, label='Vektor u')
ax2.quiver(0, 0, v2[0], v2[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color2, width=0.008, label='Vektor v')

ax2.set_xlim(-1.5, 1.5)
ax2.set_ylim(-1.5, 1.5)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)
ax2.set_title('Cosine Similarity = 0\nVinkel = 90°', 
              fontsize=12, pad=20)
ax2.axhline(y=0, color='k', linewidth=0.5)
ax2.axvline(x=0, color='k', linewidth=0.5)

# Calculate cosine similarity
cos_sim_2 = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Case 3: Cosine similarity = -1 (180 degrees)
ax3 = axes[2]
# Two opposite vectors
v1 = np.array([1, 0])
v2 = np.array([-1, 0])

ax3.quiver(0, 0, v1[0], v1[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color1, width=0.008, label='Vektor u')
ax3.quiver(0, 0, v2[0], v2[1], angles='xy', scale_units='xy', scale=1, 
           color=vector_color2, width=0.008, label='Vektor v')

ax3.set_xlim(-1.5, 1.5)
ax3.set_ylim(-1.5, 1.5)
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)
ax3.set_title('Cosine Similarity = -1\nVinkel = 180°\n"Mindst mulige sammenlignelighed"', 
              fontsize=12, pad=20)
ax3.axhline(y=0, color='k', linewidth=0.5)
ax3.axvline(x=0, color='k', linewidth=0.5)

# Calculate cosine similarity
cos_sim_3 = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# Adjust layout and save
plt.tight_layout()
plt.savefig('cosine_similarity_visualization.png', dpi=300, bbox_inches='tight')
plt.show()

print("Visualization saved as 'cosine_similarity_visualization.png'")
print("\nCosine similarity calculations:")
print(f"Case 1 (0°): {cos_sim_1:.1f}")
print(f"Case 2 (90°): {cos_sim_2:.1f}")
print(f"Case 3 (180°): {cos_sim_3:.1f}")
