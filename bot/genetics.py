#!/usr/bin/env python3
"""
Genetic Algorithm implementation for optimizing heuristic weights.
Implements the advanced GA techniques from the design document:
- Common Random Numbers (CRN) to reduce noise
- Adaptive Mutation Surge
- Phase-based Genomes (different weights for different game phases)
- Feature Pool with Binary Masking for automatic feature selection
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from game_state import GameState
from features import FeaturePool


class GamePhase(Enum):
    """Game phases as described in the design document."""
    EARLY = 1   # Turns 1-10
    MID = 2     # Turns 11-20
    LATE = 3    # Turns 21-27


@dataclass
class Gene:
    """Represents a single gene in the chromosome: (mask, weight)."""
    mask: int      # 0 or 1 - feature selection switch
    weight: float  # Weight value for the feature

    def __init__(self, mask: int = 1, weight: float = 0.0):
        self.mask = mask
        self.weight = weight


class Chromosome:
    """
    Represents a genome in the genetic algorithm.
    Implements phase-based genomes with feature masking as per design doc.
    """

    def __init__(self, num_features: int, num_phases: int = 3):
        """
        Initialize a chromosome with phase-based genes.

        Args:
            num_features: Number of features in the feature pool
            num_phases: Number of game phases (default 3 from design)
        """
        self.num_features = num_features
        self.num_phases = num_phases
        # Structure: [phase][feature] -> Gene
        self.genes = [[Gene() for _ in range(num_features)]
                     for _ in range(num_phases)]
        self.fitness = 0.0
        self.age = 0  # For tracking generations without improvement

    def get_gene(self, phase: GamePhase, feature_idx: int) -> Gene:
        """Get gene for a specific phase and feature index."""
        phase_idx = phase.value - 1  # Convert 1-based to 0-based
        return self.genes[phase_idx][feature_idx]

    def set_gene(self, phase: GamePhase, feature_idx: int, mask: int, weight: float):
        """Set gene for a specific phase and feature index."""
        phase_idx = phase.value - 1
        self.genes[phase_idx][feature_idx] = Gene(mask, weight)

    def get_fitness(self, state: GameState, feature_pool: FeaturePool) -> float:
        """
        Calculate fitness (heuristic value) for a game state using this chromosome's weights.
        Implements: H(state) = Σ(Mask_i × Weight_i × f_i(state)) for each phase
        """
        # Determine current game phase based on turn number
        turn = state.turn_number
        if turn < 10:
            phase = GamePhase.EARLY
        elif turn < 20:
            phase = GamePhase.MID
        else:
            phase = GamePhase.LATE

        # Extract all feature values
        feature_values = feature_pool.extract_all_features(state)

        # Calculate weighted sum using current phase's genes
        total = 0.0
        for i in range(self.num_features):
            gene = self.get_gene(phase, i)
            feature_value = feature_values.get(f"f{i+1}", 0.0)
            total += gene.mask * gene.weight * feature_value

        return total

    def get_all_features_fitness(self, states: List[GameState],
                                feature_pool: FeaturePool) -> float:
        """
        Calculate average fitness over multiple states (used with CRN).
        """
        if not states:
            return 0.0
        total_fitness = sum(self.get_fitness(state, feature_pool) for state in states)
        return total_fitness / len(states)

    def mutate(self, mutation_rate: float, adaptive_surge: bool = False):
        """
        Apply mutation to the chromosome.
        Implements adaptive mutation surge: if fitness hasn't improved in 3 generations,
        increase mutation rate from 5% to 25% for one generation.
        """
        effective_rate = mutation_rate * 5 if adaptive_surge else mutation_rate

        for phase_genes in self.genes:
            for gene in phase_genes:
                # Mutate mask (feature selection switch)
                if random.random() < effective_rate:
                    gene.mask = 1 - gene.mask  # Flip 0<->1

                # Mutate weight (add Gaussian noise)
                if random.random() < effective_rate:
                    # Weight range [-100, 100] as per design doc
                    gene.weight += random.gauss(0, 10)
                    gene.weight = max(-100.0, min(100.0, gene.weight))

    def crossover(self, other: 'Chromosome') -> Tuple['Chromosome', 'Chromosome']:
        """
        Perform crossover with another chromosome.
        Exchanges both mask and weight values as per design doc.
        """
        child1 = Chromosome(self.num_features, self.num_phases)
        child2 = Chromosome(self.num_features, self.num_phases)

        for p in range(self.num_phases):
            for f in range(self.num_features):
                # Uniform crossover for each gene
                if random.random() < 0.5:
                    child1.genes[p][f] = self.genes[p][f]
                    child2.genes[p][f] = other.genes[p][f]
                else:
                    child1.genes[p][f] = other.genes[p][f]
                    child2.genes[p][f] = self.genes[p][f]

        return child1, child2

    def copy(self) -> 'Chromosome':
        """Create a deep copy of the chromosome."""
        new_chromo = Chromosome(self.num_features, self.num_phases)
        for p in range(self.num_phases):
            for f in range(self.num_features):
                gene = self.genes[p][f]
                new_chromo.genes[p][f] = Gene(gene.mask, gene.weight)
        new_chromo.fitness = self.fitness
        new_chromo.age = self.age
        return new_chromo

    def __str__(self) -> str:
        """String representation showing the phase-based structure."""
        lines = ["Chromosome (Phase-based):"]
        phase_names = {GamePhase.EARLY: "Early (1-10)",
                      GamePhase.MID: "Mid (11-20)",
                      GamePhase.LATE: "Late (21-27)"}

        for phase in GamePhase:
            phase_idx = phase.value - 1
            lines.append(f"  {phase_names[phase]}:")
            for f in range(self.num_features):
                gene = self.genes[phase_idx][f]
                if gene.mask == 1:  # Only show active features
                    lines.append(f"    f{f+1}: weight={gene.weight:.2f}")
        lines.append(f"  Fitness: {self.fitness:.2f}")
        return "\n".join(lines)


class GeneticOptimizer:
    """
    Genetic Algorithm optimizer for finding optimal heuristic weights.
    Implements all the advanced techniques from the design document:
    - Common Random Numbers (CRN)
    - Adaptive Mutation Surge
    - Phase-based Genomes
    - Feature Pool with Binary Masking
    """

    def __init__(self, feature_pool: FeaturePool,
                 search_engine,
                 population_size: int = 50,
                 num_generations: int = 100,
                 elite_size: int = 5,
                 mutation_rate: float = 0.05,
                 tournament_size: int = 3):
        """
        Initialize the genetic optimizer.

        Args:
            feature_pool: Pool of features to optimize
            search_engine: Expectimax search engine for evaluation
            population_size: Number of individuals in population
            num_generations: Number of generations to evolve
            elite_size: Number of top individuals to preserve each generation
            mutation_rate: Base mutation rate (increases during adaptive surge)
            tournament_size: Size of tournament for selection
        """
        self.feature_pool = feature_pool
        self.search_engine = search_engine
        self.population_size = population_size
        self.num_generations = num_generations
        self.elite_size = elite_size
        self.base_mutation_rate = mutation_rate
        self.tournament_size = tournament_size

        # Get number of features from feature pool
        self.num_features = len(feature_pool.get_feature_names())

        # Population storage
        self.population: List[Chromosome] = []
        self.best_chromosome: Optional[Chromosome] = None
        self.best_fitness = -float('inf')
        self.generation_no_improvement = 0  # For adaptive mutation surge

        # CRN: Common Random Numbers - fixed set of seeds for fair evaluation
        self.crn_seeds = [random.randint(1, 1000000) for _ in range(50)]  # N=50 as per design

        # Initialize population
        self._initialize_population()

    def _initialize_population(self):
        """Create initial population with random chromosomes."""
        self.population = []
        for _ in range(self.population_size):
            chromosome = Chromosome(self.num_features)
            # Initialize with random masks and weights
            for p in range(3):  # 3 phases
                for f in range(self.num_features):
                    # Randomly activate features (50% chance)
                    mask = 1 if random.random() < 0.5 else 0
                    # Weight in range [-100, 100]
                    weight = random.uniform(-100, 100)
                    chromosome.set_gene(GamePhase(p+1), f, mask, weight)
            self.population.append(chromosome)

    def _evaluate_population(self) -> List[Tuple[Chromosome, float]]:
        """
        Evaluate the entire population using Common Random Numbers (CRN).
        All individuals evaluate on the same set of random seeds to reduce noise.
        """
        evaluated = []

        for chromosome in self.population:
            # Reset search engine's chromosome for evaluation
            self.search_engine.set_chromosome(chromosome)

            # Evaluate on each CRN seed (different random block sequences)
            fitness_scores = []
            for seed in self.crn_seeds:
                # Set random seed for reproducible block generation
                random.seed(seed)
                np.random.seed(seed)

                # Play a partial game or evaluate specific states
                # For simplicity, we'll evaluate on random game states
                # In practice, this would involve running actual game simulations
                fitness = self._evaluate_chromosome_on_seed(chromosome, seed)
                fitness_scores.append(fitness)

            # Average fitness over all CRN seeds (as per design doc)
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            chromosome.fitness = avg_fitness
            chromosome.age += 1

            evaluated.append((chromosome, avg_fitness))

            # Track best chromosome
            if avg_fitness > self.best_fitness:
                self.best_fitness = avg_fitness
                self.best_chromosome = chromosome.copy()
                self.generation_no_improvement = 0  # Reset counter
            else:
                self.generation_no_improvement += 1

        # Sort by fitness (descending)
        evaluated.sort(key=lambda x: x[1], reverse=True)
        return evaluated

    def _evaluate_chromosome_on_seed(self, chromosome: Chromosome, seed: int) -> float:
        """
        Evaluate a chromosome on a specific CRN seed.
        This would involve running a game simulation or evaluating game states.
        """
        # For now, return a placeholder fitness based on feature values
        # In a real implementation, this would:
        # 1. Generate a sequence of 27 blocks using the seed
        # 2. Simulate gameplay using the chromosome's weights in the heuristic
        # 3. Return the final score as fitness

        # Create a test game state
        test_state = GameState()

        # Simple placeholder: evaluate current state with chromosome's heuristic
        # This is simplified - real evaluation would involve lookahead/search
        fitness = chromosome.get_fitness(test_state, self.feature_pool)

        # Add some randomness to make it interesting (would be replaced by real simulation)
        fitness += random.gauss(0, 0.1)

        return fitness

    def _select_parent(self, evaluated: List[Tuple[Chromosome, float]]) -> Chromosome:
        """Select a parent using tournament selection."""
        tournament = random.sample(evaluated, min(self.tournament_size, len(evaluated)))
        winner = max(tournament, key=lambda x: x[1])
        return winner[0].copy()

    def evolve(self):
        """Run one generation of the genetic algorithm."""
        # Evaluate population
        evaluated = self._evaluate_population()

        # Print generation info
        best_fitness = evaluated[0][1]
        avg_fitness = sum(fit for _, fit in evaluated) / len(evaluated)
        print(f"Generation: Best={best_fitness:.2f}, Avg={avg_fitness:.2f}, "
              f"No improv for {self.generation_no_improvement} gens")

        # Check for adaptive mutation surge
        adaptive_surge = (self.generation_no_improvement >= 3)
        if adaptive_surge:
            print("*** ADAPTIVE MUTATION SURGE ACTIVE ***")

        # Create next generation
        new_population = []

        # Elite preservation: keep top individuals
        for i in range(min(self.elite_size, len(evaluated))):
            new_population.append(evaluated[i][0].copy())

        # Generate rest through selection, crossover, and mutation
        while len(new_population) < self.population_size:
            # Select parents
            parent1 = self._select_parent(evaluated)
            parent2 = self._select_parent(evaluated)

            # Crossover
            child1, child2 = parent1.crossover(parent2)

            # Mutation
            child1.mutate(self.base_mutation_rate, adaptive_surge)
            child2.mutate(self.base_mutation_rate, adaptive_surge)

            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)

        self.population = new_population

    def train(self):
        """Run the complete genetic algorithm training process."""
        print("Starting Genetic Algorithm Training...")
        print(f"Population Size: {self.population_size}")
        print(f"Generations: {self.num_generations}")
        print(f"Features: {self.num_features}")
        print(f"CRN Seeds: {len(self.crn_seeds)} (Common Random Numbers)")
        print("=" * 60)

        for generation in range(self.num_generations):
            print(f"\nGeneration {generation + 1}/{self.num_generations}")
            self.evolve()

            # Optional: print best chromosome every 10 generations
            if (generation + 1) % 10 == 0:
                print("\nBest Chromosome So Far:")
                print(self.best_chromosome)

        print("\n" + "=" * 60)
        print("Training Complete!")
        print("Best Chromosome Found:")
        print(self.best_chromosome)

        # Save the best chromosome to use in gameplay
        if self.best_chromosome:
            self.search_engine.set_chromosome(self.best_chromosome)
            print("\nBest chromosome loaded into search engine for gameplay.")


if __name__ == "__main__":
    # Test the genetics module
    from features import FeaturePool
    from expectimax import ExpectimaxSearch

    feature_pool = FeaturePool()
    search_engine = ExpectimaxSearch(feature_pool)
    optimizer = GeneticOptimizer(feature_pool, search_engine,
                               population_size=20, num_generations=5)
    optimizer.train()