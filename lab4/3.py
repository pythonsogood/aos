import pygame

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Mouse Interaction")
clock = pygame.time.Clock()
running = True

while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.MOUSEMOTION:
			x, y = event.pos
			print(f"Mouse position: ({x}, {y})")
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				print("Left mouse button clicked")
			elif event.button == 3:
				print("Right mouse button clicked")
		elif event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1:
				print("Left mouse button released")
			elif event.button == 3:
				print("Right mouse button released")

	pygame.display.flip()

	clock.tick(60)

pygame.quit()
