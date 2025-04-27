import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import math
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import entropy

def load_anonymized_data(file_path):
    """Load the anonymized data from CSV file."""
    return pd.read_csv(file_path)

def identify_quasi_identifiers(df):
    """Identify quasi-identifiers (columns with non-* values)."""
    quasi_ids = []
    for col in df.columns:
        if not df[col].eq('*').all():
            quasi_ids.append(col)
    return quasi_ids

def compute_equivalence_classes(df, quasi_identifiers):
    """Compute equivalence classes based on quasi-identifiers."""
    # Create a composite key for each record based on quasi-identifiers
    ec_keys = df[quasi_identifiers].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
    
    # Count frequency of each equivalence class
    ec_counts = Counter(ec_keys)
    
    # Group records by equivalence class
    ec_groups = defaultdict(list)
    for i, key in enumerate(ec_keys):
        ec_groups[key].append(i)
    
    return ec_counts, ec_groups

def calculate_reidentification_risks(ec_counts):
    """Calculate re-identification risk metrics."""
    risks = []
    for ec_size in ec_counts.values():
        risks.append(1.0 / ec_size)
    
    max_risk = max(risks) if risks else 0
    avg_risk = sum(risks) / len(risks) if risks else 0
    
    return {
        'max_risk': max_risk,
        'avg_risk': avg_risk,
        'risks': risks
    }

def calculate_equivalence_class_metrics(ec_counts, total_records):
    """Calculate metrics related to equivalence classes."""
    ec_sizes = list(ec_counts.values())
    
    # Count records in equivalence classes of size 1 (unique records)
    unique_records = sum(1 for size in ec_sizes if size == 1)
    
    return {
        'num_equivalence_classes': len(ec_sizes),
        'min_ec_size': min(ec_sizes) if ec_sizes else 0,
        'max_ec_size': max(ec_sizes) if ec_sizes else 0,
        'avg_ec_size': sum(ec_sizes) / len(ec_sizes) if ec_sizes else 0,
        'unique_records': unique_records,
        'unique_records_percentage': unique_records / total_records * 100 if total_records > 0 else 0,
        'ec_size_distribution': Counter(ec_sizes)
    }

def calculate_information_loss(df, quasi_identifiers):
    """Calculate information loss metrics for the anonymized data."""
    info_loss = {}
    
    for col in quasi_identifiers:
        # Count number of distinct generalized values
        distinct_values = df[col].nunique()
        
        # Count *'s and generalized values
        generalized_count = 0
        asterisk_count = 0
        
        for val in df[col]:
            if val == '*':
                asterisk_count += 1
            elif '**' in str(val):  # Check for partial generalization
                generalized_count += 1
        
        # Calculate column-specific information loss
        total_records = len(df)
        info_loss[col] = {
            'distinct_values': distinct_values,
            'asterisk_percentage': (asterisk_count / total_records) * 100 if total_records > 0 else 0,
            'generalized_percentage': (generalized_count / total_records) * 100 if total_records > 0 else 0,
            'total_loss_percentage': ((asterisk_count + generalized_count) / total_records) * 100 if total_records > 0 else 0
        }
    
    # Calculate average information loss across all quasi-identifiers
    avg_loss = sum(col_loss['total_loss_percentage'] for col_loss in info_loss.values()) / len(info_loss) if info_loss else 0
    
    info_loss['average'] = avg_loss
    
    return info_loss

def calculate_suppression_rate(df):
    """Calculate the rate of suppressed values in the dataset."""
    total_cells = df.size
    suppressed_cells = (df == '*').sum().sum()
    
    return suppressed_cells / total_cells * 100 if total_cells > 0 else 0

def discernibility_metric(ec_groups, total_records):
    """Calculate the discernibility metric."""
    dm = 0
    for ec in ec_groups.values():
        dm += len(ec) ** 2
    
    return dm

def evaluate_k_anonymity(df, k):
    """
    Evaluate if the dataset satisfies k-anonymity and return associated metrics.
    
    Args:
        df: DataFrame containing the anonymized data
        k: The k value to test against
        
    Returns:
        Dictionary containing evaluation results
    """
    # Identify quasi-identifiers
    quasi_identifiers = identify_quasi_identifiers(df)
    
    # Compute equivalence classes
    ec_counts, ec_groups = compute_equivalence_classes(df, quasi_identifiers)
    
    # Calculate risk metrics
    risks = calculate_reidentification_risks(ec_counts)
    
    # Calculate equivalence class metrics
    ec_metrics = calculate_equivalence_class_metrics(ec_counts, len(df))
    
    # Calculate information loss
    info_loss = calculate_information_loss(df, quasi_identifiers)
    
    # Calculate suppression rate
    suppression_rate = calculate_suppression_rate(df)
    
    # Calculate discernibility metric
    dm = discernibility_metric(ec_groups, len(df))
    
    # Check if k-anonymity is satisfied
    satisfies_k_anonymity = ec_metrics['min_ec_size'] >= k
    
    # Compile results
    results = {
        'k_value': k,
        'quasi_identifiers': quasi_identifiers,
        'num_records': len(df),
        'satisfies_k_anonymity': satisfies_k_anonymity,
        'risks': risks,
        'equivalence_class_metrics': ec_metrics,
        'information_loss': info_loss,
        'suppression_rate': suppression_rate,
        'discernibility_metric': dm
    }
    
    return results

def visualize_results(results):
    """Create visualizations for the evaluation results."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Risk distribution
    risks = results['risks']['risks']
    if risks:
        sns.histplot(risks, bins=20, kde=True, ax=axes[0, 0])
        axes[0, 0].set_title('Re-identification Risk Distribution')
        axes[0, 0].set_xlabel('Risk (1/|EC|)')
        axes[0, 0].set_ylabel('Frequency')
    
    # Equivalence class size distribution
    ec_dist = results['equivalence_class_metrics']['ec_size_distribution']
    sizes = list(ec_dist.keys())
    counts = list(ec_dist.values())
    
    axes[0, 1].bar(sizes, counts)
    axes[0, 1].set_title('Equivalence Class Size Distribution')
    axes[0, 1].set_xlabel('Equivalence Class Size')
    axes[0, 1].set_ylabel('Number of Equivalence Classes')
    
    # Information loss by attribute
    attr_loss = {attr: loss['total_loss_percentage'] 
                 for attr, loss in results['information_loss'].items() 
                 if attr != 'average'}
    
    if attr_loss:
        attrs = list(attr_loss.keys())
        values = list(attr_loss.values())
        
        axes[1, 0].barh(attrs, values)
        axes[1, 0].set_title('Information Loss by Attribute')
        axes[1, 0].set_xlabel('Information Loss (%)')
        axes[1, 0].set_xscale('log')
    
    # Summary metrics
    summary_metrics = [
        f"Satisfies k-anonymity (k={results['k_value']}): {results['satisfies_k_anonymity']}",
        f"Maximum Re-identification Risk: {results['risks']['max_risk']*100:.2f}%",
        f"Average Re-identification Risk: {results['risks']['avg_risk']*100:.2f}%",
        f"Number of Equivalence Classes: {results['equivalence_class_metrics']['num_equivalence_classes']}",
        f"Minimum Equivalence Class Size: {results['equivalence_class_metrics']['min_ec_size']}",
        f"Average Equivalence Class Size: {results['equivalence_class_metrics']['avg_ec_size']:.2f}",
        f"Unique Records: {results['equivalence_class_metrics']['unique_records']} ({results['equivalence_class_metrics']['unique_records_percentage']:.2f}%)",
        f"Average Information Loss: {results['information_loss']['average']:.2f}%",
        f"Suppression Rate: {results['suppression_rate']:.2f}%",
        f"Discernibility Metric: {results['discernibility_metric']}"
    ]
    
    axes[1, 1].axis('off')
    axes[1, 1].text(0, 0.5, '\n'.join(summary_metrics), fontsize=10)
    
    plt.tight_layout()
    plt.savefig('k_anonymity_evaluation.png')
    plt.close()

def print_evaluation_report(results):
    """Print a detailed evaluation report."""
    print("\n" + "="*60)
    print(f"K-ANONYMITY EVALUATION REPORT (k = {results['k_value']})")
    print("="*60)
    
    print("\n1. DATASET OVERVIEW")
    print("-" * 20)
    print(f"Total Records: {results['num_records']}")
    print(f"Quasi-identifiers: {', '.join(results['quasi_identifiers'])}")
    print(f"Satisfies k-anonymity (k={results['k_value']}): {results['satisfies_k_anonymity']}")
    
    print("\n2. PRIVACY PROTECTION METRICS")
    print("-" * 30)
    print(f"Maximum Re-identification Risk: {results['risks']['max_risk']*100:.2f}%")
    print(f"Average Re-identification Risk: {results['risks']['avg_risk']*100:.2f}%")
    
    print("\n3. EQUIVALENCE CLASS METRICS")
    print("-" * 30)
    print(f"Number of Equivalence Classes: {results['equivalence_class_metrics']['num_equivalence_classes']}")
    print(f"Minimum Equivalence Class Size: {results['equivalence_class_metrics']['min_ec_size']}")
    print(f"Maximum Equivalence Class Size: {results['equivalence_class_metrics']['max_ec_size']}")
    print(f"Average Equivalence Class Size: {results['equivalence_class_metrics']['avg_ec_size']:.2f}")
    print(f"Unique Records: {results['equivalence_class_metrics']['unique_records']} ({results['equivalence_class_metrics']['unique_records_percentage']:.2f}%)")
    
    print("\n4. INFORMATION LOSS METRICS")
    print("-" * 30)
    print(f"Average Information Loss: {results['information_loss']['average']:.2f}%")
    print("Information Loss by Attribute:")
    for attr, loss in results['information_loss'].items():
        if attr != 'average':
            print(f"  - {attr}: {loss['total_loss_percentage']:.2f}%")
    
    print(f"\nSuppression Rate: {results['suppression_rate']:.2f}%")
    print(f"Discernibility Metric: {results['discernibility_metric']}")
    
    print("\n5. RECOMMENDATIONS")
    print("-" * 20)
    
    if not results['satisfies_k_anonymity']:
        print(f"⚠️ The dataset does NOT satisfy k-anonymity for k={results['k_value']}.")
        print(f"   Minimum equivalence class size is {results['equivalence_class_metrics']['min_ec_size']} (should be ≥ {results['k_value']}).")
    else:
        print(f"✓ The dataset satisfies k-anonymity for k={results['k_value']}.")
    
    if results['risks']['max_risk'] > 0.5:
        print(f"⚠️ Maximum re-identification risk is high ({results['risks']['max_risk']*100:.2f}%).")
    
    if results['equivalence_class_metrics']['unique_records'] > 0:
        print(f"⚠️ There are {results['equivalence_class_metrics']['unique_records']} unique records in the dataset.")
    
    print("\n" + "="*60)

def main():
    # File path to the anonymized data
    file_path = 'anonymized_data.csv'
    
    try:
        # Load the anonymized data
        df = load_anonymized_data(file_path)
        
        # Evaluate for different k values
        for k in [2, 3, 5]:
            results = evaluate_k_anonymity(df, k)
            print_evaluation_report(results)
            visualize_results(results)
            
            # Save results to CSV
            with open(f'k{k}_anonymity_results.csv', 'w') as f:
                f.write("Metric,Value\n")
                f.write(f"K Value,{k}\n")
                f.write(f"Satisfies K-Anonymity,{results['satisfies_k_anonymity']}\n")
                f.write(f"Maximum Re-identification Risk,{results['risks']['max_risk']*100:.2f}%\n")
                f.write(f"Average Re-identification Risk,{results['risks']['avg_risk']*100:.2f}%\n")
                f.write(f"Number of Equivalence Classes,{results['equivalence_class_metrics']['num_equivalence_classes']}\n")
                f.write(f"Minimum Equivalence Class Size,{results['equivalence_class_metrics']['min_ec_size']}\n")
                f.write(f"Average Equivalence Class Size,{results['equivalence_class_metrics']['avg_ec_size']:.2f}\n")
                f.write(f"Unique Records Percentage,{results['equivalence_class_metrics']['unique_records_percentage']:.2f}%\n")
                f.write(f"Average Information Loss,{results['information_loss']['average']:.2f}%\n")
                f.write(f"Suppression Rate,{results['suppression_rate']:.2f}%\n")
                f.write(f"Discernibility Metric,{results['discernibility_metric']}\n")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()